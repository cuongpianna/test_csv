import scrapy
from datetime import datetime
from scrapy import Request
import html2text
from urllib.parse import urljoin
from dateutil import parser
import urllib.parse
import re

from demo.items import NewsItem


class CorporateFinanceReviewSpider(scrapy.Spider):
    name = 'CorporateFinanceReview'
    start_urls = ['https://taichinhdoanhnghiep.net.vn/tin-tuc/']
    base_url = 'https://taichinhdoanhnghiep.net.vn/'

    def parse(self, response):
        posts = response.xpath('//div[@class="web-cat-left lt"]//article/h3/a/@href')
        if posts:
            for post in posts:
                yield Request(post.extract(), callback=self.parse_post)

        if not response.xpath('//a[@class="page active"]'):
            page = response.xpath('//div[@class="grNextPage __MB_ARTICLE_PAGING lt"]/a[2]/@href').get()
            if page:
                url = response.url + page
                yield response.follow(url)
        else:
            page = response.xpath(
                '//div[@class="grNextPage __MB_ARTICLE_PAGING lt"]/a[@class="page active"]/following-sibling::a[1]/@href').get()
            if page:
                url = response.url.replace(re.search(r'\/p[\d]+', response.url).group(0), '')
                url = urllib.parse.urljoin(url, page)
                yield response.follow(page)

    def parse_post(self, response):
        time_format, short_date = self.parse_date(response)
        item = NewsItem(
            title=response.xpath('//h1[@title]/text()').get().strip(),
            timestamp=time_format,
            content_html=response.xpath('//*[@id="noidung"]').get(),
            body=html2text.html2text(response.xpath('//*[@id="noidung"]').get()),
            link=response.url,
            subhead=html2text.html2text(response.xpath('//*[@id="noidung"]/h2').get()),
            pic=self.parse_pictures(response),
            date=short_date,
            author=response.xpath('//cite/text()').get()
        )
        yield item

    def parse_date(self, response):
        if response.xpath('//span[@class="bx-time lt"]/text()').get():
            raw_time = response.xpath('//span[@class="bx-time lt"]/text()').get().strip()
            true_time = parser.parse(raw_time)
            publish_date = datetime(year=true_time.year, minute=true_time.minute, hour=true_time.hour,
                                    day=true_time.day,
                                    month=true_time.month)
            return publish_date.isoformat(), '{}/{}/{}'.format(true_time.month, true_time.day, true_time.year)
        return '', ''

    def parse_pictures(self, response):
        urls = response.xpath('//*[@id="noidung"]//img/@src').extract()
        urls = [urljoin(self.base_url, item) for item in urls]
        captions = response.xpath('//*[@id="noidung"]//img/@alt').extract()
        res = [i + '|' + j for i, j in zip(urls, captions)]
        if urls:
            result = '&&'.join(res)
            return result
        else:
            return ''
