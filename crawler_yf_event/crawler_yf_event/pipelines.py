# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
import json
from datetime import datetime
import os


class CrawlerYfEventPipeline:
    def __init__(self):
        self.all_data = []

    def process_item(self, item, spider):
        # 데이터 전처리
        processed_item = {}
        for key, value in item.items():
            if isinstance(value, str):
                processed_item[key] = value.strip()
            elif value is None:
                processed_item[key] = ''
            else:
                processed_item[key] = value
        
        self.all_data.append(processed_item)
        return item

    def close_spider(self, spider):
        try:
            if self.all_data:
                filename = 'yf_calendar_events.json'
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(self.all_data, f, indent=2, ensure_ascii=False)
                spider.logger.info(f'Saved {len(self.all_data)} items to {filename}')
            else:
                spider.logger.warning('No data to save')

        except Exception as e:
            spider.logger.error(f'Error saving data: {str(e)}')
