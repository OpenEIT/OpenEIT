# coding: utf-8
# pylint: disable=no-member, invalid-name, too-many-arguments
# pylint: disable=unused-argument, unused-variable, function-redefined
""" plot function based on vispy.visuals for tetrahedral plots """
from __future__ import absolute_import

# vispy
from vispy.visuals import CompoundVisual
from vispy.visuals.mesh import MeshVisual
from vispy.visuals.line import LineVisual
from vispy.visuals.markers import MarkersVisual
from vispy.color import Color


# build your visual
class TetVisual(CompoundVisual):
    """ display a 3D mesh """

    def __init__(self,
                 vertices=None, simplices=None, vertex_colors=None,
                 edge_color=None, edge_width=1,
                 markers=None, marker_colors=None, marker_size=1,
                 **kwargs):
        """
        a mesh visualization toolkit that can also plot edges or markers

        Parameters
        ----------

        Notes
        -----
        """
        self._mesh = MeshVisual()
        self._edge = LineVisual()
        self._edge_color = Color(edge_color)
        self._marker = MarkersVisual()
        #
        self._vertex_colors = vertex_colors

        self._update()
        # initialize visuals
        CompoundVisual.__init__(self,
                                [self._mesh, self._edge, self._marker],
                                **kwargs)
        # set default state, 'opaque', 'translucent' or 'additive'
        self._mesh.set_gl_state(preset='translucent',
                                blend=True,
                                depth_test=False,
                                cull_face=False,
                                polygon_offset_fill=True,
                                polygon_offset=(1, 1))
        # end
        self.freeze()

        def _update(self):
            """
            update parameters to visuals
            """
            pass

        @property
        def edge_color(self):
            """ get """
            return self._edge_color

        @edge_color.setter
        def edge_color(self, edge_color):
            """ set """
            self._edge_color = Color(edge_color)
            self._update()
