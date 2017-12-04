from django.http import HttpResponse,  HttpResponseRedirect
from django.views.generic import TemplateView
from django.template import Context
from django.template.loader import get_template
from django.contrib.auth.models import User
from django.conf import settings
from django import template
from django.shortcuts import render


from bs4 import BeautifulSoup
from urlparse import urlparse
import urllib2
import extraction
import requests
import urllib3
import urllib, cStringIO
import json

register = template.Library()


def getImages(self,buff1):
	soup = BeautifulSoup(buff1)
	img_list = soup.findAll('meta', {"property":'og:image'})
	imgTags = soup.findAll('img')
	og = [tag['content'] for tag in img_list]
	img = []
	for tag in imgTags:
		if 'src' in tag: 
			img.append(tag['src'])
	line = soup.find_all('img', attrs={'data-a-dynamic-image': True})
	for i in line:
		a = re.findall(r"['\"](.*?)['\"]", i['data-a-dynamic-image'], re.DOTALL)
		if len(a) > 0:
			print a[-1]
			img.append(a[-1])
	for i in img:
		og.append(i)
	#reverses list, doesn't return copy
	og.reverse()
	return og

class ExtractView(TemplateView):

	template = "extractor/base.html"

	def get(self, request, *args, **kwargs):
		context =dict()
		context["username"] = request.user.username
		html = render(request,self.template,context)
		return HttpResponse(html)

	def post(self, request, *args, **kwargs):

		if request.is_ajax():

			urlText = request.POST["url-search"]

			headers={'User-Agent': 'Chrome/41.0.2228.0 Safari/537.36'}
			cookies = dict(cookies_are='working')
			session = requests.session()

			html = session.get(urlText,headers=headers,cookies=cookies).text
			extracted = extraction.Extractor().extract(html, source_url=urlText)

			context = dict()
			images = []

			parsed_uri = urlparse(urlText)
			domain = '{uri.scheme}://{uri.netloc}/'.format(uri=parsed_uri)

			for image in extracted.images:
				images.append(image)

			if "authors" in extracted._unexpected_values:
				context["author"] = extracted._unexpected_values["authors"][0]
			elif "author" in extracted._unexpected_values:
				context['author'] = extracted._unexpected_values["author"]

			filimage = getImages(html)

			image_groupA = filter(lambda pic: pic.startswith('data') == False , filimage)
			image_groupB = filter(lambda pic: pic.startswith('data') == False, extracted.images)

			filteredImages =image_groupA + image_groupB

			#check duplicate
			cleanedImages =  list(filteredImages)
			if extracted.image not in cleanedImages:
				cleanedImages.insert(0,extracted.image)
			else:
				cleanedImages.remove(extracted.image)
				cleanedImages.insert(1,extracted.image)

			context["images"] = cleanedImages
			context["imagesthumb"] = cleanedImages
			context["image"]  = extracted.image
			context["title"] = extracted.title
			context["description"] = extracted.description
			context["domain"] = domain
			context["url"] = urlText

			html = render(request,self.template,context)
			return html
		else:
			return HttpResponse(status=400)

