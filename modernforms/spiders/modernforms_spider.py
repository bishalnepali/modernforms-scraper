import json
import scrapy
import re
import urllib
import ast

class ModernformsSpiderSpider(scrapy.Spider):
    name = 'modernforms'
    start_urls = ['http://modernforms.com/']
    headers = {
    'authority': 'www.modernforms.com',
    'sec-ch-ua': '" Not A;Brand";v="99", "Chromium";v="99", "Google Chrome";v="99"',
    'accept': '*/*',
    'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
    'x-requested-with': 'XMLHttpRequest',
    'sec-ch-ua-mobile': '?0',
    'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.74 Safari/537.36',
    'sec-ch-ua-platform': '"macOS"',
    'origin': 'https://www.modernforms.com',
    'sec-fetch-site': 'same-origin',
    'sec-fetch-mode': 'cors',
    'sec-fetch-dest': 'empty',
    'referer': 'https://www.modernforms.com/product-category/vanity-lights/',
    'accept-language': 'en-GB,en-US;q=0.9,en;q=0.8',
    # Requests sorts cookies= alphabetically
    # 'cookie': 'cookielawinfo-checkbox-necessary=yes; cookielawinfo-checkbox-non-necessary=yes; _ga=GA1.2.167195825.1647902822; _gid=GA1.2.1866973747.1647902822; __zlcmid=196knDyBHIg4bvx; _gat_gtag_UA_40618632_1=1',
}
    def parse(self, response):
        list_of_category = response.xpath("//article[contains(@class, 'LUMINAIRES')]//section[@class='sub-thumb-container']/figure/a/@href").extract()
        for category in list_of_category:
            if 'product-category' in category:
                yield scrapy.Request(category, callback=self.parse_category)

    
    def parse_category(self, response):
        
        first_page = response.meta.get('first_page', True)
        if first_page:
            products = response.xpath('//aside[@class="thumb-box product-box"]/a/@href').extract()
            counting_page = 12
            try:
                data = re.findall("style='display:none'>(.*)</idUnfiltered>",response.text)[0]
                total_products = re.findall("idUnfiltered data-total='(.*)' style",response.text)[0]
                cat_id = response.xpath("//title/text()").get().split()[0]
            except Exception as e:
                print(e)
                breakpoint()
        else:
            counting_page = response.meta.get('counting_page')
            data = response.meta.get('data', '')
            total_products = response.meta.get('total_products')
            cat_id = response.meta.get('cat_id')
            counting_page = int(counting_page) + 12
            products = [item['link'] for item in response.json()]

        for product in products[:1]:
            yield scrapy.Request(product, callback=self.parse_product)
        if counting_page < int(total_products):
            form_data = {
                'data': data,
                'page': str(counting_page),
                'catID': str(cat_id),
            }
            headers = self.headers.copy()
            headers['referer'] = response.url
            params = {
                'action': 'lazyUnfiltered',
            }
            yield scrapy.FormRequest(f"https://www.modernforms.com/wp-admin/admin-ajax.php?{urllib.parse.urlencode(params)}", method="POST", formdata=form_data, headers=headers, callback=self.parse_category, meta={'data': data, 'total_products': total_products, 'counting_page': counting_page, 'cat_id': cat_id, 'first_page': False})

    def parse_product(self, response, **kwargs):
        title = response.xpath('//section/h2/text()').extract_first().strip()
        models = re.findall('var all_models =(.*);',response.text)[0].strip()
        models_list = ast.literal_eval(models)
        downloads = [{download.xpath('./text()').extract_first().strip():download.xpath('./@href').extract_first()} for download in response.xpath("//button[@class='download-btn']/following-sibling::ul/li/a")]
        features = ';'.join(response.xpath("//ul[@id='default-wac-feature-list']/li/text()").extract())
        cct = response.xpath("//section[@data-panel='second']/img/@data-src").get()
        certifications = ';'.join(response.xpath("//div[@class='sertcs']//img/@data-src").extract())
        images = response.xpath("//section[@class='product-thumbs']/section/figure/img/@data-src").extract()
        for model in models_list:
            yield {
                'title': title,
                'model': model.get('zstyle'),
                'size': model.get('zsize'),
                'color_temp': model.get('zcct_desc'),

                'downloads': downloads,
                'features': features,
                'cct': cct,
                'certifications': certifications,
                'images': images,
            }

        

