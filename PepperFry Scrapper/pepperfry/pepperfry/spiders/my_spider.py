import scrapy
import re
import os
import json
import requests

class pepperfrySpider(scrapy.Spider):
    name = "pepperfrySpider"
    BASE_DIR = './Pepperfry_data/'
    MAX_CNT = 20
    

    def start_requests(self):

    	BASE_URL = "https://www.pepperfry.com/site_product/search?q="

    	items = ["two seater sofa","bench","book cases","coffee table","dining set","queen beds","arm chairs","chest drawers","garden seating","bean bags","king beds"]

    	urls = []
    	dir_names = []

    	for item in items:
    		query_string = '+'.join(item.split(' '))
    		dir_name = '-'.join(item.split(' '))
    		dir_names.append(dir_name)
    		urls.append(BASE_URL+query_string)

    		dir_path = self.BASE_DIR+dir_name
    		if not os.path.exists(dir_path):
    			os.makedirs(dir_path)
    	


    	for i in range(len(urls)):
    		d = {
    			"dir_name": dir_names[i]
    		}
    		resp =  scrapy.Request(url=urls[i],callback=self.parse,dont_filter=True)
    		resp.meta['dir_name'] = dir_names[i]
    		yield resp


    def parse(self, response,**meta):
    	#response.selector.xpath('').extract()
        product_urls = response.xpath('//div/div/div/a[@p=0]/@href').extract()
        #print(product_urls)
        #print(len(product_urls))
        counter = 0

        #print(response.meta)
        for url in product_urls:
        	resp =  scrapy.Request(url=url,callback=self.parse_item,dont_filter=True)
        	resp.meta['dir_name'] = response.meta['dir_name']
        	#print(resp)

        	if counter == self.MAX_CNT:
        		break

        	if not resp == None:
        		counter +=1
        		#print(resp)

        	yield resp
       
    def parse_item(self,response,**meta):

    	item_title = response.xpath('//div/div/div/h1/text()').extract()[0]
    	item_price = response.xpath('//div/div/div/p/b[@class="pf-orange-color pf-large font-20 pf-primary-color"]/text()').extract()[0].strip()
    	#item_mrp  = response.xpath('//span[@class="vip-old-price-amt font-15 pf-text-grey "]/text()').extract()[0].strip()
    	item_savings = response.xpath('//p[@class="pf-margin-0 pf-bold-txt font-13"]/text()').extract()[0].strip()
    	item_description = response.xpath('//div[@itemprop="description"]/div/p/text()').extract()
    	#item_description = '\n'.join(item_description[:-2]) #Remove the last two lines of pepper fry
    	item_detail_keys = response.xpath('//div[@id="itemDetail"]/p/b/text()').extract()
    	item_detail_values = response.xpath('//div[@id="itemDetail"]/p/text()').extract() #Remove the "DETAILS" word

    	brand = itemprop=response.xpath('//span[@itemprop="brand"]/text()').extract()
    	item_detail_values[0] = brand[0] #Brand is fetched separately

    	stop_words = ["(all dimensions in inches)","(all dimensions in inches )","( all dimensions in inches)"]
    	item_detail_values = [word.strip() for word in item_detail_values if word not in stop_words]

    	a = len(item_detail_keys)
    	b =  len(item_detail_values)
    	idetail = {}
    	
    	#Generate a Dictionary of Key Values Pairs of Item Details
    	for i in range(min(a,b)):
    		idetail[item_detail_keys[i]] = item_detail_values[i]

    	#print(idetail) 


    	#print("Details :")
    	#print(item_detail_keys)
    	#print(item_detail_values)
    	#print(item_details)
    	stop_items = ["pepperfry.com","We also offer you a","So go ahead and buy with confidence.","Brand will upfront contact you for assembly"]
    	item_description = filter(lambda x: all([not y.lower() in x.lower() for y in stop_items]),item_description)
    	item_description = '\n'.join(item_description)
    	image_url_list = response.xpath('//li[@class="vip-options-slideeach"]/a/@data-img').extract()
    	
    	#print(type(item_title))
    	#print(type(item_description))
    	

    	#Scrap product if it has atleast 4 images
    	if(len(image_url_list)>3):
	    	d = {
	    		'Item Title':item_title,
	    		'description':item_description,
	    		'Item Price':item_price,
	    		'Savings' :item_savings,
	    		'Details':idetail
	    	}
	    	#print("Category :",response.meta['dir_name'])
	    	CATEGORY_NAME = response.meta['dir_name']
	    	ITEM_DIR_URL = os.path.join(self.BASE_DIR,os.path.join(CATEGORY_NAME,item_title))  
	    	if not os.path.exists(ITEM_DIR_URL):
	    		os.makedirs(ITEM_DIR_URL)
	    	
	    	#Save Metadata

	    	with open(os.path.join(ITEM_DIR_URL,'metadata.txt'),'w') as f:
	    		json.dump(d,f)

	    	#Save Images
	    	for i,img_url in enumerate(image_url_list):
	    		r = requests.get(img_url)
	    		with open(os.path.join(ITEM_DIR_URL,"image_{}.jpg".format(i)),'wb') as f:
	    			f.write(r.content)

	    	#print(item_title)
	    	print("--> Successfully saved \""+item_title+"\" data at :"+ITEM_DIR_URL)
	    	#Return the dictionary if product was choose, NONE otherwise
	    	yield d
    	
    	yield None

