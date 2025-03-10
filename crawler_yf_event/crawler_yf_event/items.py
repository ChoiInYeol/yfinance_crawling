# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class YFCalendarEventItem(scrapy.Item):
    event_type = scrapy.Field()  # earnings, economic, ipo, splits
    crawl_date = scrapy.Field()

    def __setitem__(self, key, value):
        # 동적으로 필드 추가
        if key not in self.fields:
            self.fields[key] = scrapy.Field()
        super().__setitem__(key, value)
