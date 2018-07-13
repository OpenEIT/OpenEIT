"""
# Look up Table that translate the incoming 
# Changes format of 8 electrode bipolar measure to tetrapolar coordinate frame. 
#
"""

def bipolar2tetra(data):

	# what is the order of the bipolar data? 
	# 
	bipolar_order = [01,02,03,04,05,06,07,12,13,14,15,16,17,23,24,25,26,27,34,35,36,37,45,46,47,56,57,67]
	
	# we take the first two numbers, and just use the first one. 
	# we take the second two numbers and just use the second one? 
	13,14,15,16,17
	20,24,25,26,27
	30, 31!!, 35, 36, 37
	40,41!!,42!!,46,47
	50,51!!, 52!!, 53!!, 57
	60,61!,62!,63!,64!
	71!,72!,73!,74!,75!

	01? (01 21), 07? (01 76)

	tetrapolar_order = 
	[12 43,12 54,12 65, 12 76, 12 07, 
	23 10, 23 54 , 23 65, 23 76, 23 07,
	34 10, 34 21, 34 65, 34 76, 34 07,
	45 10, 45 21, 45 32, 45 76, 45 07, 
	56 10, 56 21, 56 32, 56 43, 56 07, 
	67 10, 67 21, 67 32, 67 43, 67 54, 
	70 21, 70 32, 70 43, 70 54, 70 65
	]

	return tetradata

"""

	16 electrode model has 208 combinations... 

	Wait, even if i got that right, I'd get it wrong as v_diff goes around in a circle. 
	
"""	



