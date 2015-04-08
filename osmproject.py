# The xml2dict() is the main function which takes in an OSM file and turns it into a dictionary that can
# be accessed by normal dicitonary queries.  Only specified elements of the file will be used to populate
# The dictionary.
def xml2dict(filename):
	import time
	import re
	import xml.etree.ElementTree as ET
	from pygeocoder import Geocoder
	expected = ["Street", "Avenue", "Boulevard", "Drive", "Court", "Place", "Square", "Lane", "Road", 
	        "Trail", "Parkway", "Commons"]
	street_type_re = re.compile(r'\b\S+\.?$', re.IGNORECASE)
	street_mapping = {"St": "Street",
			            "St.": "Street",
			            "Ave" : "Avenue",
			            "Rd." : "Road",
			            "Rd" : "Road",
			            "SE" : "Southeast",
			            "S.E." : "Southeast",
			            "NE" : "Northeast",
			            "S" : "South",
			            "Dr" : "Drive",
			            "Rd/Pkwy" : "Road/Parkway",
			            "Ln" : "Lane",
			            "Dr." : "Drive",
			            "E" : "East",
			            "Pl" : "Plain",
			            "ne" : "Northeast",
			            "NW" : "Northwest",
			            "Ave." : "Avenue",
			            "N." : "North",
			            "W" : "West",
			            "Pkwy" : "Parkway",
			            "Ter" : "Terrace",
			            "Pky" : "Parkway",
			            "SW" : "Southwest",
			            "N" : "North",
			            "Blvd" : "Boulevard"}
	city_mapping = {"Minneapolis, MN" : "Minneapolis",
					"St. Anthony" : "Saint Anthony",
					"St. Paul" : "Saint Paul",
					"St Anthony" : "Saint Anthony",
					"St Paul" : "Saint Paul"}            
	CREATED = [ "version", "changeset", "timestamp", "user", "uid"]
	address = ['addr:unit', 'addr:full','addr:housenumber', 'addr:postcode', 'addr:street', 
				'addr:city', 'addr:state', 'addr:country',
				'addr:suite', 'addr:housename']
	# The shape_element() function takes in iterations of 'ET.iterparse'.  Each iteration is a line in the OSM xml file
	# and will move forward in the function if the line has a tag that equals 'node' or 'way'.	      
	def shape_element(element):
		# First a dictionary is created.  This dictionary will recieve the cleaned data from the OSM file
		# and then returned at the end.		
	    node = {}
	    # First we check if the tag is either 'node' or 'way'.
	    if element.tag == "node" or element.tag == "way" :
	    	# Then we create a key called 'type' which equals either 'node' or 'way'.
	        node['type'] = element.tag
			# Then we check every attribute in the line. 
			# If an attribute matches any value in CREATED, we create a dictionary called 'created'.
			# The loop breaks immedietly after the match and creation of the dictionary.
	        for i in element.attrib.keys():
	            if i in CREATED:
	                node['created'] = {}
	                break
			# Once the 'created' dictionary is created.  The attributes which match the values in CREATED and their
			# respective values are added to the dictionary 'created'.  Attributes that equal 'lat' or 'lon' are skipped.
			# The rest of the attributes are made into keys in the node dictionary with values being their respective
			# value pair.
	        for i in element.attrib.keys():
	            if i in CREATED:
	                node['created'][i] = element.attrib[i]
	            elif i == 'lon' or i == 'lat':
	                continue
	            else:
	                node[i] = element.attrib[i]
			# If 'lat' is one of the attributes in the element, it is assumed it has a 'lon' pair as well.
			# These two values are combined in a list [Latitude, Longitude].  A key, 'pos', is created in the
			# node dictionary with its value being the [Latitude, Longitude] list.
	        if 'lat' in element.attrib.keys():
	            node['pos'] = [float(element.attrib['lat']), float(element.attrib['lon'])]
			# The following scans the 'k' values of the subelements of 'node' or 'way' tags and creates a dictionary
			# depending on the matches.
			# For example, if scanning the 'k' values reveal a value that starts with 'gnis:'
			# the code will create a dictionary 'gnis' inside the node dictionary
	        for i in element:
	            if 'k' in i.attrib:
	                if i.attrib['k'] in address:
	                    node['address'] = {}
	                elif i.attrib['k'].startswith('metcouncil:'):
	                    node['metcouncil'] = {}
	                elif i.attrib['k'].startswith('tiger:'):
	                	node['tiger'] = {}
	                elif i.attrib['k'].startswith('metrogis:'):
	                	node['metrogis'] = {}
	                elif i.attrib['k'].startswith('umn:'):
	                	node['umn'] = {}
	                elif i.attrib['k'].startswith('gnis:'):
	                	node['gnis'] = {}
			# Some of the Latitudenal and Longitudenal data are not located in the parent levels of 'node' and 'way'
			# In particular, if the subelements' 'k' values include items that start with 'umn:', the corresponding
			# locational data is located in 'umn:BuildingCenterXYLatitude' and 'umn:BuildingCenterXYLongitude'
			# The following code extracts those values and includes them in the 'pos' list.
	        for i in element:
	        	if 'k' in i.attrib:
	        		if i.attrib['k'] in ['umn:BuildingCenterXYLatitude', 'umn:BuildingCenterXYLongitude']:
	        			node['pos'] = []
	        			break
	        for i in element:
        		if 'k' in i.attrib:
        			if i.attrib['k'] == 'umn:BuildingCenterXYLatitude':
        				node['pos'].append(float(i.attrib['v']))
        				break
        	for i in element:
        		if 'k' in i.attrib:
        			if i.attrib['k'] == 'umn:BuildingCenterXYLongitude':
        				node['pos'].append(float(i.attrib['v']))
        				break
			# As instructed in lesson 6, some of the subelements whose tags are 'ref' need to be grouped
			# under the list 'node_refs'.  The following creates that list.
	        for i in element:
	            if 'ref' in i.attrib:
	                node['node_refs'] = []
			# The following code populates the previously created groups in the node dictionary
			# by scanning the subelements and tests the existence of the necessary value-pairs.
			# If the necessary value-pairs exist, the 'k' value prefix is stripped and added
			# as a key under the respective group.  Then the 'v' is added as teh value/
			# For example. 'k' = 'addr:street', 'v' = 'dorland' is added as
			# 'street' : 'dorland'
	        for i in element:
	            if 'k' in i.attrib:
	                if i.attrib['k'] in address:
	                	if i.attrib['k'] == 'addr:city':
	                		if i.attrib['v'] in city_mapping.keys():
	                			node['address'][re.sub('addr:', '', i.attrib['k'])] = city_mapping[i.attrib['v']]
	                		else:
	                			node['address'][re.sub('addr:', '', i.attrib['k'])] = i.attrib['v']
	                	else:
	                		node['address'][re.sub('addr:', '', i.attrib['k'])] = i.attrib['v']
	                elif i.attrib['k'].startswith('metcouncil:'):
	                    node['metcouncil'][re.sub('metcouncil:', '', i.attrib['k'])] = i.attrib['v']
	                elif i.attrib['k'].startswith('tiger:'):
	                	node['tiger'][re.sub('tiger:', '', i.attrib['k'])] = i.attrib['v']
	                elif i.attrib['k'].startswith('metrogis:'):
	                	node['metrogis'][re.sub('metrogis:', '', i.attrib['k'])] = i.attrib['v']
	                elif (i.attrib['k'].startswith('umn:') and
	                		i.attrib['k'] not in ['umn:BuildingCenterXYLatitude', 'umn:BuildingCenterXYLongitude']):
	                	node['umn'][re.sub('umn:', '', i.attrib['k'])] = i.attrib['v']
	                elif i.attrib['k'].startswith('gnis:'):
	                	node['gnis'][re.sub('gnis:', '', i.attrib['k'])] = i.attrib['v']
	                elif ('addr:street:' in i.attrib['k'] or
	                		i.attrib['k'] in ['umn:BuildingCenterXYLatitude', 'umn:BuildingCenterXYLongitude']):
	                    continue
	                else:
	                    # All the remaining value pairs are then added with the 'k' value being the key
	                    # and the 'v' value being the value of that key
	                    node[i.attrib['k']] = i.attrib['v']
	            # Earlier we created the 'node_refs' list inside the node dictionary
	            # The following will add the values to this list.
	            if 'ref' in i.attrib:
	                node['node_refs'].append(i.attrib['ref'])
	        # Finally after the node dictionary is created from the particular iteration of ET.iterparse(),
	        # it is returned
	        return node
	# 2 empty lists are created.  We will append each dictionary returned by feeding the iterations of the OSM
	# file into shape_element() into the 'temp' list.  Since some of the iterations will not contain the tags
	# 'node' and 'way', the shape_element() will return 'None' for these instances.
	# We will then run throught each iteration of temp and only append the iterations that contains information
	# to the data list.
	temp = []
	data = []
	for _, element in ET.iterparse(filename):
	    temp.append(shape_element(element))
	for i in temp:
		if i != None:
			data.append(i)
	# The following corrects the street values fo the data.  We run through each iteration of the data list.
	# If the iteration contains a key 'address', we move forward and check if the key 'address' contains a key
	# 'street'.  If these conditions are met, we check the street value's suffix is in the keys of 'street_mapping'.
	# If it is, the code replaces that word for the value of the key it matches.
	for i in data:
		if 'address' in i:
			if 'street' in i['address']:
				search = street_type_re.search(i['address']['street'])
				if search:
					if street_type_re.search(i['address']['street']).group() in street_mapping.keys():
						data[data.index(i)]['address']['street'] = re.sub(street_type_re.search(i['address']['street']).group(), 
																			street_mapping[street_type_re.search(i['address']['street']).group()], 
																			data[data.index(i)]['address']['street'])
	# The following corrects the incorrect postal codes.  We run through each iteration of the data list.
	# The first 'if' statement checks if the iteration has the keys 'address' and 'pos'
	# If so, we proceed to check if the postal code is incorrect.
	# If it is, we use the coordinates in the 'pos' list and apply it to the Geocoder.reverse_geocode()
	# The postal code from that query will replace the incorrect postal code.
	#
	# The second 'elif' statement is for iterations that have an 'address' but do not have a 'pos' list
	# to reverse_geocode() the postal code.
	# It instead will use the Geocoder.geocode() function and search specific elements of the 'address'
	# key to return the correct postal code.
	for i in data:
		if 'address' in i and 'pos' in i:
		    if 'postcode' in i['address']:
		        if len(i['address']['postcode']) < 5 or re.search('[a-zA-Z]', i['address']['postcode']):
		            results = Geocoder.reverse_geocode(i['pos'][0], i['pos'][1])
		            i['address']['postcode'] = str(results.postal_code)
		elif 'address' in i and 'pos' not in i:
			if 'postcode' in i['address']:
				if len(i['address']['postcode']) < 5 or re.search('[a-zA-Z]', i['address']['postcode']):
					q = ''
					if 'housename' in i['address']:
						q = i['address']['housename'] + ' MN'
					elif 'housenumber' in i['address'] and 'street' in i['address']:
						q = i['address']['housenumber'] + ' ' + i['address']['street'] + ' MN'
					results = Geocoder.geocode(q)
					i['address']['postcode'] = str(results.postal_code)
	# The following will standardize 2 part postal codes to 1 part postal codes.
	# For example, 55404-1234 will be turned to 55404
	for i in data:
	    if 'address' in i:
	    	if 'postcode' in i['address']:
	    		if len(i['address']['postcode']) > 5:
	    			i['address']['postcode'] = i['address']['postcode'][0:5]
	# The cleaned and sorted data is ready to be returned.
	return data

# The dict2json() simply takes the dictionary produced by xml2dict() and saves it as the specified
# file in .json format
def dict2json(dict, output_file):
	import codecs
	import json
	with codecs.open(output_file, 'w') as fo:
	    for i in dict:
	        fo.write(json.dumps(i) + '\n')
	fo.close()

# The audit_xml() scans through the original OSM file, which is formatted in XML
# and returns a specified dictionary of audits
def audit_xml(filename, form = 'all', value = None):
	import xml.etree.ElementTree as ET
	# count_attrib() will count the unique values of each element in the file
	def count_attrib(filename):
		attrib_count = {}
		for _, element in ET.iterparse(filename):
			if element.tag in ['node', 'way', 'tag', 'nd']:
			    for i in element.attrib.keys():
			        if i not in attrib_count.keys():
			            attrib_count[i] = {'count' : 1}
			        else:
			            attrib_count[i]['count'] += 1
		return attrib_count
	# count_val() will count a specific value within the file
	def count_val(x, filename):
		k = {}
		for _, element in ET.iterparse(filename):
			if element.tag in ['node', 'way', 'tag', 'nd']:
			    if x in element.attrib:
			        if element.attrib[x] not in k:
			            k[element.attrib[x]] = 1
			        else:
			            k[element.attrib[x]] += 1
		return k
	# tag_count simply counts the unique tags located in the file
	def tag_count(filename):
		tags = {}
		for _, element in ET.iterparse(filename):
			if element.tag in ['node', 'way', 'tag', 'nd']:
				for i in element:
					if i.tag not in tags:
						tags[i.tag] = 1
					else:
						tags[i.tag] += 1
		return tags
	# depending on the 'form' and/or 'value' argument, audit_xml() will return the desired
	# audit type
	if form.lower() == 'all':
		data = {}
		attrib = count_attrib(filename)
		for i in attrib:
			data[i] = count_val(i, filename)
		for i in data:
			data[i]['TOTAL'] = attrib[i]['count']
		data['TAGS'] = tag_count(filename)
		return data
	elif form.lower() == 'tags':
		return tag_count(filename)
	elif form.lower() == 'attributes':
		return count_attrib(filename)
	elif form.lower() == 'values':
		return count_val(v, filename)
	else:
		if not form or form not in ['all', 'tags', 'attributes', 'values']:
			print "Invalid Audit Type"