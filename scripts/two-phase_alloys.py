
'''
==================================================================================================
Script to calculate the IPA dielectric function of two-phase binary alloys (A_{1-x}B_{x})
==================================================================================================
method:
-- average: mixture of dielectric function of the two phases weighted by the alloy composition
-- refractive: mixture of refractive index of the two phases weighted by the alloy composition
-- bruggeman: compute dielectric function of the alloy using Bruggeman theory

sys.argv[1] = method
sys.argv[2] = composition (atomic fraction)
sys.argv[3] = A
sys.argv[4] = B
sys.argv[5] = file name with dielectric function of A
sys.argv[6] = file name with dielectric function of B
'''

import os , json , sys
import numpy as np
import math
import colour


procedure = sys.argv[1]

# atomic fraction of element B
x = float(sys.argv[2])

element_a = sys.argv[3]
element_b = sys.argv[4]

eps_filename_a = sys.argv[5]
eps_filename_b = sys.argv[6]

## Here I take epsilon interband from the outputfile of Yambo
data_a = np.genfromtxt(eps_filename_a)
energies_a  = data_a[:,0]
eps_im_a = data_a[:,1]
eps_re_a = data_a[:,2]

data_b = np.genfromtxt(eps_filename_b)
energies_b  = data_b[:,0]
eps_im_b = data_b[:,1]
eps_re_b = data_b[:,2]


# Check that the energy intervals of the two elements are the same
if len(energies_a) != len(energies_b):
   print 'Error: different number of energy values!'
   sys.exit() 
#for i in xrange(len(energies_a)-1):
#    if round(energies_a[i],2) != round(energies_b[i],2):
#        print 'Error: different energy values!'
#        sys.exit()

energies = energies_a

if procedure == 'average':

    eps_im = (1.0 - x)*eps_im_a + x*eps_im_b
    eps_re = (1.0 - x)*eps_re_a + x*eps_re_b

    norm_epsilon = np.sqrt(eps_re**2 + eps_im**2)
    refractive_index = np.sqrt( ( eps_re + norm_epsilon  ) / 2. )
    extint_coeff = np.sqrt( ( -eps_re + norm_epsilon  ) / 2. )

elif procedure == 'bruggeman':

    eps_a = eps_re_a + 1j*eps_im_a
    eps_b = eps_re_b + 1j*eps_im_b
    eps_1 = 1./4. * (    np.sqrt(   ( -3*eps_a*x +2*eps_a + 3*eps_b*x - eps_b )**2 + 8*eps_a*eps_b  )   -3*eps_a*x + 2*eps_a + 3*eps_b*x - eps_b)
    eps_2 = 1./4. * (  - np.sqrt(   ( -3*eps_a*x +2*eps_a + 3*eps_b*x - eps_b )**2 + 8*eps_a*eps_b  )   -3*eps_a*x + 2*eps_a + 3*eps_b*x - eps_b)

    eps_re = []
    eps_im = []
    for i in xrange(len(energies)):
        if eps_1.imag[i]>0.0 and eps_2.imag[i]<0.0:
            eps_re.append(eps_1.real[i])
            eps_im.append(eps_1.imag[i])
        elif eps_2.imag[i]>0.0 and eps_1.imag[i]<0.0:
            eps_re.append(eps_2.real[i])
            eps_im.append(eps_2.imag[i])
        else:
            print i, eps_1.imag[i], eps_2.imag[i]
            #sys.exit('Error in solving Bruggeman equation')
    eps_re = np.array(eps_re)
    eps_im = np.array(eps_im)

    norm_epsilon = np.sqrt(eps_re**2 + eps_im**2)
    refractive_index = np.sqrt( ( eps_re + norm_epsilon  ) / 2. )
    extint_coeff = np.sqrt( ( -eps_re + norm_epsilon  ) / 2. )

elif procedure == 'refractive':

    norm_epsilon_a = np.sqrt(eps_re_a**2 + eps_im_a**2)
    refractive_index_a = np.sqrt( ( eps_re_a + norm_epsilon_a  ) / 2. )
    extint_coeff_a = np.sqrt( ( -eps_re_a + norm_epsilon_a  ) / 2. )

    norm_epsilon_b = np.sqrt(eps_re_b**2 + eps_im_b**2)
    refractive_index_b = np.sqrt( ( eps_re_b + norm_epsilon_b  ) / 2. )
    extint_coeff_b = np.sqrt( ( -eps_re_b + norm_epsilon_b  ) / 2. )

    refractive_index = (1.0 - x)*refractive_index_a + x*refractive_index_b
    extint_coeff = (1.0 - x)*extint_coeff_a + x*extint_coeff_b


else:
    sys.exit()

reflectivity = ( (refractive_index - 1)**2 + extint_coeff**2 ) / ( (refractive_index + 1)**2 + extint_coeff**2 )
    
alloy = '{}{}{}{}'.format(element_a, 1.0-x, element_b, x)

if procedure == 'average' or procedure == 'bruggeman':
    with open('epsilon_{}.dat'.format(alloy),'w') as o: 
        for i in xrange(len(energies)-1):
            o.write(str(energies[i]))
            o.write('  '+str(eps_im[i]))
            o.write('  '+str(eps_re[i]))
            o.write('\n')

## I write to file: reflectivity
with open('reflectivity_{}.dat'.format(alloy),'w') as o: 
    for i in xrange(len(energies)-1):
        o.write(str(energies[i]))
        o.write('  '+str(reflectivity[i]))
        o.write('\n')

# Reflectivity as a function of the wavelength
wavelengths_nm = 1239.8 / energies # in nm
with open('reflectivity_{}_lambda.dat'.format(alloy),'w') as o: 
    for i in xrange(len(wavelengths_nm)-1):
        o.write(str(wavelengths_nm[i]))
        o.write('  '+str(reflectivity[i]))
        o.write('\n')


### Calculate colour coordinates

# take the files with the D65 and the CMFs from the folder of the colour module 
file_d65illuminant = '{}/D65_illuminant_1nm.dat'.format(os.path.dirname(colour.__file__))    
file_cmf = '{}/cmf_1nm.dat'.format(os.path.dirname(colour.__file__)) 
        
# calculate colour using the colour module
colours = colour.calcColour(energies, reflectivity, file_d65illuminant, file_cmf, do_plot=False)
colours.pop('Fit_residuals')
        
# write colour coordinates to file in json format
with open('colour_{}.dat'.format(alloy),'w') as o:
    json.dump(colours, o, indent=4)
            
