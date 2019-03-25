# OpenEIT Dashboard

Biomedical Imaging has previously been expensive and near impossible to hack and experiment with. If more people experimented and understood how imaging works we could move it forward much faster and make these transformative technologies available to everyone. OpenEIT(EIT is for electrical impedance tomography) uses non-ionizing AC current to recreate an image of any conductive material, such as your lungs, arm or head, using the same tomographic reconstruction technique as a CATSCAN. The PCB is only 2" square, with bluetooth, making it a portable and hackable way to do biomedical imaging!

##  How to install the python dashboard. 

## Requirements
```
Python 3.6.7+
```

## Install
```
pip install -r requirements.txt

```

Note: If you are having an install problem first try to install the anaconda environment which ensures windows/linux or OSX environments are configured correctly: https://www.anaconda.com/download/ 

## Run
```
python app.py
```
You should now see the server running through the console at a server location accessible by any internet browser at Running on http://127.0.0.1:8050/. To see the dashboard open a browser window(I use chrome) to this address.

The dashboard should now be open and running and look like this: 

<p align="center">
	<img src="images/software.png" height="400">
</p>

## Functionality 

The dashboard can connect to the SPECTRA device via Bluetooth or Serial connection, do tomographic reconstructions in real-time, or by reading in offline data. You can also record data for later analysis. We suggest you have a look in the tutorials to try time series, bioimpedance spectroscopy and electrical impedance tomography functionality. [Tutorials](https://openeitgithubio.readthedocs.io/en/latest/)

<p align="center">
	<img src="images/eit32.jpeg" height="300">
</p>


In the root OpenEIT folder there are a couple of extra scripts which are helpful when doing analysis. 

# offline.py 

Is an example of how to read in offline data for analysis outside the dashboard. 

# simdata.py 

Simdata creates data in the same format as the hardware device, incase you want to do simulations before collecting real data. 

You can also use the main software to do either time series or bioimpedance spectroscopy. Instructions for these can be found in the readthedocs tutorials. 

<p align="center">
	<img src="images/LungscomparedtoCTScan.png" height="300">
</p>

## Algorithms 

There are three classic EIT algorithms implemented - Back Projection, Graz Consensus and Gauss Newton Methods using the pyEIT toolbox - [pyEIT](https://github.com/liubenyuan/pyEIT). Each has many parameters which can be adjusted to get better results. It's also possible to create 3D meshes with this software in a similar manner to EIDORS(a matlab based EIT software suite). 

## License 

The Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License seems to fit best with this project. Check out the human readable summary here: 

<a rel="license" href="http://creativecommons.org/licenses/by-nc-sa/4.0/"><img alt="Creative Commons License" style="border-width:0" src="https://i.creativecommons.org/l/by-nc-sa/4.0/88x31.png" /></a><br />This work is licensed under a <a rel="license" href="http://creativecommons.org/licenses/by-nc-sa/4.0/">Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License</a>.

If you'd like to make a derivative of this project in a commercial setting, we'd love a payment in exchange for a commercial license so that we can afford to spend time both maintaining this project and making more projects like this one. If this hybrid open source model works, it would enable open source projects to receive some funding, making the global commons stronger to benefit everyone. 




