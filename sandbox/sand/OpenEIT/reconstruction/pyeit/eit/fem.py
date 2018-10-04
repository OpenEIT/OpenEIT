# coding: utf-8
# pylint: disable=invalid-name, no-member, too-many-locals
# pylint: disable=too-many-instance-attributes
""" 2D/3D FEM routines """
# Copyright (c) Benyuan Liu. All Rights Reserved.
# Distributed under the (new) BSD License. See LICENSE.txt for more info.
from __future__ import division, absolute_import, print_function

from collections import namedtuple
import numpy as np
import numpy.linalg as la
from scipy import sparse

from .utils import eit_scan_lines


class Forward(object):
    """ FEM forward computing code """

    def __init__(self, mesh, el_pos):
        """
        A good FEM forward solver should only depend on
        mesh structure and the position of electrodes
        NOTE: the nodes are assumed continuous numbered.

        Parameters
        ----------
        mesh : dict
            mesh structure
        el_pos : NDArray
            numbering of electrodes positions
        """
        self.pts = mesh['node']
        self.tri = mesh['element']
        self.tri_perm = mesh['perm']
        self.el_pos = el_pos

        # reference electrodes [ref node should not be on electrodes]
        ref_el = 0
        while ref_el in self.el_pos:
            ref_el = ref_el + 1
        self.ref = ref_el

        # infer dimensions from mesh
        self.n_pts, self.n_dim = self.pts.shape
        self.n_tri, self.n_vertices = self.tri.shape
        self.ne = el_pos.size

    def solve_eit(self, ex_mat=None, step=1, perm=None, parser=None):
        """
        EIT simulation, generate perturbation matrix and forward v

        Parameters
        ----------
        ex_mat : NDArray
            numLines x n_el array, stimulation matrix
        step : int
            the configuration of measurement electrodes (default: adjacent)
        perm : NDArray
            Mx1 array, initial x0. must be the same size with self.tri_perm
        parser : str
            if parser is 'fmmu', within each stimulation pattern, diff_pairs
            or boundary measurements are re-indexed and started
            from the positive stimulus electrode
            if parser is 'std', subtract_row start from the 1st electrode

        Returns
        -------
        jac : NDArray
            number of measures x n_E complex array, the Jacobian
        v : NDArray
            number of measures x 1 array, simulated boundary measures
        b_matrix : NDArray
            back-projection mappings (smear matrix)
        """
        # initialize/extract the scan lines (default: apposition)
        if ex_mat is None:
            ex_mat = eit_scan_lines(16, 8)

        # initialize the permittivity on element
        if perm is None:
            perm0 = self.tri_perm
        elif np.isscalar(perm):
            perm0 = np.ones(self.n_tri, dtype=np.float)
        else:
            assert perm.shape == (self.n_tri,)
            perm0 = perm

        # calculate f and Jacobian iteratively over all stimulation lines
        jac, v, b_matrix = [], [], []
        n_lines = ex_mat.shape[0]

        for i in range(n_lines):
            # FEM solver of one stimulation pattern, a row in ex_mat
            ex_line = ex_mat[i]
            f, jac_i = self.solve(ex_line, perm0)
            f_el = f[self.el_pos]

            # boundary measurements, subtract_row-voltages on electrodes
            diff_op = voltage_meter(ex_line, n_el=self.ne,step=step, parser=parser)
            
            # print ('ex_mat')
            # print (ex_line)
            # print (diff_op)

            v_diff = subtract_row(f_el, diff_op)
            jac_diff = subtract_row(jac_i, diff_op)

            # build bp projection matrix
            # 1. we can either smear at the center of elements, using
            #    >> fe = np.mean(f[self.tri], axis=1)
            # 2. or, simply smear at the nodes using f
            b = smear(f, f_el, diff_op)

            # append
            v.append(v_diff)
            jac.append(jac_diff)
            b_matrix.append(b)

        # update output, now you can call p.jac, p.v, p.b_matrix
        pde_result = namedtuple("pde_result", ['jac', 'v', 'b_matrix'])
        p = pde_result(jac=np.vstack(jac),
                       v=np.hstack(v),
                       b_matrix=np.vstack(b_matrix))
        return p

    def solve(self, ex_line, perm):
        """
        with one pos (A), neg(B) driven pairs, calculate and
        compute the potential distribution (complex-valued)

        Parameters
        ex_line : NDArray
            stimulation (scan) patterns/lines
        perm : NDArray
            permittivity on elements (initial)

        Returns
        -------
        f : NDArray
            potential on nodes
        J : NDArray
            Jacobian
        """
        # 1. calculate local stiffness matrix (on each element)
        ke = calculate_ke(self.pts, self.tri)

        # 2. assemble to global K
        kg = assemble_sparse(ke, self.tri, perm, self.n_pts, ref=self.ref)

        # 3. calculate electrode impedance matrix R = K^{-1}
        r_matrix = la.inv(kg)
        r_el = r_matrix[self.el_pos]

        # 4. solving nodes potential using boundary conditions
        b = self._natural_boundary(ex_line)
        f = np.dot(r_matrix, b).ravel()

        # 5. build Jacobian matrix column wise (element wise)
        #    Je = Re*Ke*Ve = (nex3) * (3x3) * (3x1)
        jac = np.zeros((self.ne, self.n_tri), dtype=perm.dtype)
        for (i, e) in enumerate(self.tri):
            jac[:, i] = np.dot(np.dot(r_el[:, e], ke[i]), f[e])

        return f, jac

    def _natural_boundary(self, ex_line):
        """
        Notes
        -----
        Generate the Neumann boundary condition. In utils.py,
        you should note that ex_line is local indexed from 0...15,
        which need to be converted to global node number using el_pos.
        """
        drv_a_global = self.el_pos[ex_line[0]]
        drv_b_global = self.el_pos[ex_line[1]]

        # global boundary condition
        b = np.zeros((self.n_pts, 1))
        b[drv_a_global] = 1.
        b[drv_b_global] = -1.

        return b


def smear(f, fb, pairs):
    """
    build smear matrix B for bp

    Parameters
    ----------
    f : NDArray
        potential on nodes
    fb : NDArray
        potential on adjacent electrodes
    pairs : NDArray
        electrodes numbering pairs

    Returns
    -------
    NDArray
        back-projection matrix
    """
    b_matrix = []
    for i, j in pairs:
        f_min, f_max = min(fb[i], fb[j]), max(fb[i], fb[j])
        b_matrix.append((f_min < f) & (f <= f_max))

    return np.array(b_matrix)


def subtract_row(v, pairs):
    """
    v_diff[k] = v[i, :] - v[j, :]

    Parameters
    ----------
    v : NDArray
        Nx1 boundary measurements vector or NxM matrix
    pairs : NDArray
        Nx2 subtract_row pairs

    Returns
    -------
    NDArray
        difference measurements
    """
    i = pairs[:, 0]
    j = pairs[:, 1]
    # row-wise/element-wise operation on matrix/vector v
    v_diff = v[i] - v[j]

    return v_diff


def voltage_meter(ex_line, n_el=16, step=1, parser=None):
    """
    extract subtract_row-voltage measurements on boundary electrodes.
    we direct operate on measurements or Jacobian on electrodes,
    so, we can use LOCAL index in this module, do not require el_pos.

    Notes
    -----
    A : current driving electrode
    B : current sink
    M, N : boundary electrodes, where v_diff = v_n - v_m

    Parameters
    ----------
    ex_line : NDArray
        2x1 array, 0 for positive electrode, 1 for negative electrode
    n_el : int
        number of electrodes
    step : int
        measurement method (which two electrodes are used for measuring)
    parser : str
        if parser is 'fmmu', data are trimmed, start index (i) is always 'A'.

    Returns
    -------
    v : NDArray
        (N-1)*2 arrays of subtract_row pairs
    """
    # local node
    drv_a = ex_line[0]
    drv_b = ex_line[1]
    i0 = drv_a if parser == 'fmmu' else 0

    # build differential pairs
    v = []
    for a in range(i0, i0 + n_el):
        m = a % n_el
        n = (m + step) % n_el
        # if any of the electrodes is the stimulation electrodes
        if not(m == drv_a or m == drv_b or n == drv_a or n == drv_b):
            # the order of m, n matters
            v.append([n, m])

    diff_pairs = np.array(v)
    return diff_pairs


def assemble(ke, tri, perm, n_pts, ref=0):
    """
    Assemble the stiffness matrix (dense matrix, default)

    Parameters
    ----------
    ke : NDArray
        n_tri x (n_dim x n_dim) 3d matrix
    tri : NDArray
        the structure of mesh
    perm : NDArray
        n_tri x 1 conductivities on elements
    n_pts : int
        number of nodes
    ref : int
        reference electrode

    Returns
    -------
    NDArray
        k_matrix, NxN array of complex stiffness matrix

    Notes
    -----
    you can use sparse matrix (IJV) format to automatically add the local
    stiffness matrix to the global matrix.
    """
    n_tri = tri.shape[0]

    # assemble global stiffness matrix
    k_global = np.zeros((n_pts, n_pts), dtype=perm.dtype)
    for ei in range(n_tri):
        k_local = ke[ei]
        pe = perm[ei]

        no = tri[ei, :]
        ij = np.ix_(no, no)
        k_global[ij] += (k_local * pe)

    # place reference electrode
    if 0 <= ref < n_pts:
        k_global[ref, :] = 0.
        k_global[:, ref] = 0.
        k_global[ref, ref] = 1.

    return k_global


def assemble_sparse(ke, tri, perm, n_pts, ref=0):
    """
    Assemble the stiffness matrix (using sparse matrix)

    Parameters
    ----------
    ke : NDArray
        n_tri x (n_dim x n_dim) 3d matrix
    tri : NDArray
        the structure of mesh
    perm : NDArray
        n_tri x 1 conductivities on elements
    n_pts : int
        number of nodes
    ref : int
        reference electrode

    Returns
    -------
    NDArray
        k_matrix, NxN array of complex stiffness matrix

    Notes
    -----
    you may use sparse matrix (IJV) format to automatically add the local
    stiffness matrix to the global matrix.
    """
    n_tri, n_vertices = tri.shape

    # New: use IJV indexed sparse matrix to assemble K (fast, prefer)
    # index = np.array([np.meshgrid(no, no, indexing='ij') for no in tri])
    # note: meshgrid is slow, using handcraft sparse index, for example
    # let tri=[[1, 2, 3], [4, 5, 6]], then indexing='ij' is equivalent to
    # row = [1, 1, 1, 2, 2, 2, ...]
    # col = [1, 2, 3, 1, 2, 3, ...]
    row = np.repeat(tri, n_vertices).ravel()
    col = np.repeat(tri, n_vertices, axis=0).ravel()
    data = np.array([ke[i] * perm[i] for i in range(n_tri)]).ravel()

    # set reference nodes before constructing sparse matrix, where
    # K[ref, :] = 0, K[:, ref] = 0, K[ref, ref] = 1.
    # write your own mask code to set the corresponding locations of data
    # before building the sparse matrix, for example,
    # data = mask_ref_node(data, row, col, ref)

    # for efficient sparse inverse (csc)
    A = sparse.csr_matrix((data, (row, col)),
                          shape=(n_pts, n_pts), dtype=perm.dtype)

    # the stiffness matrix may not be sparse
    A = A.toarray()

    # place reference electrode
    if 0 <= ref < n_pts:
        A[ref, :] = 0.
        A[:, ref] = 0.
        A[ref, ref] = 1.

    return A


def calculate_ke(pts, tri):
    """
    Calculate local stiffness matrix on all elements.

    Parameters
    ----------
    pts : NDArray
        Nx2 (x,y) or Nx3 (x,y,z) coordinates of points
    tri : NDArray
        Mx3 (triangle) or Mx4 (tetrahedron) connectivity of elements

    Returns
    -------
    ke_array : NGArray
        n_tri x (n_dim x n_dim) 3d matrix
    """
    n_tri, n_vertices = tri.shape

    # check dimension
    # '3' : triangles
    # '4' : tetrahedrons
    if n_vertices == 3:
        _k_local = _k_triangle
    elif n_vertices == 4:
        _k_local = _k_tetrahedron
    else:
        raise TypeError('The num of vertices of elements must be 3 or 4')

    # default data types for ke
    ke_array = np.zeros((n_tri, n_vertices, n_vertices))
    for ei in range(n_tri):
        no = tri[ei, :]
        xy = pts[no]

        # compute the KIJ (permittivity=1.)
        ke = _k_local(xy)
        ke_array[ei] = ke

    return ke_array


def _k_triangle(xy):
    """
    given a point-matrix of an element, solving for Kij analytically
    using barycentric coordinates (simplex coordinates)

    Parameters
    ----------
    xy : NDArray
        (x,y) of nodes 1,2,3 given in counterclockwise manner

    Returns
    -------
    ke_matrix : NDArray
        local stiffness matrix
    """
    # edges (vector) of triangles
    s = xy[[2, 0, 1]] - xy[[1, 2, 0]]
    # s1 = xy[2, :] - xy[1, :]
    # s2 = xy[0, :] - xy[2, :]
    # s3 = xy[1, :] - xy[0, :]

    # area of triangles
    # TODO: remove abs, user must make sure all triangles are CCW.
    # at = 0.5 * la.det(s[[0, 1]])
    at = np.abs(0.5 * det2x2(s[0], s[1]))

    # (e for element) local stiffness matrix
    ke_matrix = np.dot(s, s.T) / (4. * at)

    return ke_matrix


def det2x2(s1, s2):
    """Calculate the determinant of a 2x2 matrix"""
    return s1[0]*s2[1] - s1[1]*s2[0]


def _k_tetrahedron(xy):
    """
    given a point-matrix of an element, solving for Kij analytically
    using barycentric coordinates (simplex coordinates)

    Parameters
    ----------
    xy : NDArray
        (x,y) of nodes 1, 2, 3, 4 given in counterclockwise manner,
        see notes.

    Returns
    -------
    ke_matrix : NDArray
        local stiffness matrix

    Notes
    -----
    A tetrahedron is described using [0, 1, 2, 3] (local node index) or
    [171, 27, 9, 53] (global index). Counterclockwise (CCW) is defined
    such that the barycentric coordinate of face (1->2->3) is positive.
    """
    s = xy[[2, 3, 0, 1]] - xy[[1, 2, 3, 0]]

    # volume of the tetrahedron
    # TODO: remove abs, user must make sure all tetrahedrons are CCW.
    vt = np.abs(1./6 * la.det(s[[0, 1, 2]]))

    # calculate area (vector) of triangle faces
    # re-normalize using alternative (+,-) signs
    ij_pairs = [[0, 1], [1, 2], [2, 3], [3, 0]]
    signs = [1, -1, 1, -1]
    a = [sign*np.cross(s[i], s[j]) for (i, j), sign in zip(ij_pairs, signs)]
    a = np.array(a)

    # local (e for element) stiffness matrix
    ke_matrix = np.dot(a, a.transpose()) / (36. * vt)

    return ke_matrix
