import os
import cloudinary.api
import random

class CloudinaryHelper:
    def __init__(self):
        self.next_cursor = ""
        self.last_pull_image_length = 0
        self.photo_urls = []
    
    def get_last_saved_cursor(self):
        return self.next_cursor

    def get_last_pull_image_length(self):
        return self.last_pull_image_length

    def get_all_available_photos(self):
        return self.photo_urls

    def get_one_random_photo(self):
        return random.choice(self.photo_urls)

    # for first pull
    def initial_pull_from_Cloudinary_server(self):
        # Connect to the Cloudinary Admin API
        res = cloudinary.api.resources(cloud_name=os.environ['CLD_USERNAME'],api_key=os.environ['CLD_API_KEY'],
                                    api_secret=os.environ['CLD_API_SECRET'],
                                    max_results="500")
        self.photo_urls.extend([x['secure_url'] for x in res['resources']])
        
        # Once exceed the 500 photos limit
        while 'next_cursor' in res:
            self.next_cursor = res['next_cursor']
            res = cloudinary.api.resources(cloud_name=os.environ['CLD_USERNAME'],api_key=os.environ['CLD_API_KEY'],
                                    api_secret=os.environ['CLD_API_SECRET'],
                                    max_results="500",next_cursor=self.next_cursor)
            self.last_pull_image_length = len(res['resources'])
            self.photo_urls.extend([x['secure_url'] for x in res['resources']])

    # for pull in command
    def consecutive_pull_from_Cloudinary_server(self):
        # Connect to the Cloudinary Admin API
        res = cloudinary.api.resources(cloud_name=os.environ['CLD_USERNAME'],api_key=os.environ['CLD_API_KEY'],
                                    api_secret=os.environ['CLD_API_SECRET'],
                                    max_results="500")

        if len(res['resources']) > self.last_pull_image_length: # keep pulling, as new images have been added
            self.last_pull_image_length = len(res['resources'])
            self.photo_urls.extend([x['secure_url'] for x in res['resources']])
            
            # Once exceed the 500 photos limit
            while 'next_cursor' in res:
                self.next_cursor = res['next_cursor']
                res = cloudinary.api.resources(cloud_name=os.environ['CLD_USERNAME'],api_key=os.environ['CLD_API_KEY'],
                                        api_secret=os.environ['CLD_API_SECRET'],
                                        max_results="500",next_cursor=self.next_cursor)
                self.last_pull_image_length = len(res['resources'])
                self.photo_urls.extend([x['secure_url'] for x in res['resources']])
