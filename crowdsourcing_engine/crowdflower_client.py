import crowdflower.client
import os
from db_engine import DBConnection
import json
from cons import CROWDFLOWER as CF
from cons import DB
import requests
import json


def dumper(obj):
    try:
        return obj.toJSON()
    except:
        return obj.__dict__


class CrowdFlower(object):

    def __init__(self):
        self.client = crowdflower.client.Client(os.getenv("CROWDFLOWER_API_KEY"))
        self.db_connection = DBConnection()
        self.api_key = os.getenv("CROWDFLOWER_API_KEY")
        self.judgements_session = requests.session()

        # self.connection = crowdflower.Connection(api_key=os.getenv("CROWDFLOWER_API_KEY"))

    def chunks(self, l, n):
        """Yield successive n-sized chunks from l."""
        for i in range(0, len(l), n):
            yield l[i:i + n]

    def get_jobs(self):
        job = self.client.get_job(1239688)
        job.cml = """
<div class="html-element-wrapper">
	<h2>The tweet you are evaluating is:</h2>
	<p>{{tweet_content}}</p>
	<h2><strong>This tweet's entities are:</strong></h2>
	<ul>
		{% for entity in entity_list %}
			<li>{{ entity_list[forloop.index0] }}</li>
		{% endfor %}
	</ul>
</div>
<cml:radios label="Do you understand the tweet?" validates="required" gold="true">
	<cml:radio label="Yes" value="yes" />
	<cml:radio label="No" value="no" />
</cml:radios>
<cml:select label="Please indicate the first entity of your relation: NOTE: THIS MUST BE DIFFERENT FROM THE SECOND ENTITY." validates="required" gold="true">
	{% for entity in entity_list %}
		<cml:option label="{{ entity_list[forloop.index0] }}" value="{{ entity_list[forloop.index0] }}" />
	{% endfor %}
</cml:select>
<cml:select label="Please indicate the second entity of your relation: NOTE: THIS MUST BE DIFFERENT FROM THE FIRST ENTITY." validates="required" gold="true">
	{% for entity in entity_list %}
		<cml:option label="{{ entity_list[forloop.index0] }}" value="{{ entity_list[forloop.index0] }}" />
	{% endfor %}
</cml:select>
<cml:text label="What is the SIMPLE relationship between the entities you have chosen" validates="required" gold="true" />
	<cml:radios label="Do you think the topic of the tweet is politically important?" validates="required" gold="true">
	<cml:radio label="Yes" value="yes" />
	<cml:radio label="No" value="no" />
</cml:radios><cml:text label="What is the first word in the tweet?" validates="required" gold="true" />
        """
        job.update()

    def get_judgements(self, job_id):
        page_no = 1
        results = self.judgements_session.get(
            url="https://api.figure-eight.com/v1/jobs/%s/judgments.json?key=%s&page=%s" %
                (job_id, self.api_key, page_no))

        content = json.loads(results.content)
        for key, result in content.iteritems():
            print result
            # json_result = json.loads(results)

    def get_fact_opinion(self, job_id):
        crowd_data = []
        tweet_list = []
        job = self.client.get_job(job_id)
        tweets = self.db_connection.find_document(collection=DB.TWEET_COLLECTION,
                                                  filter={"$and": [
                                                      {"created_at_epoch": {"$gt": 1520812800}},
                                                      {"created_at_epoch": {"$lt": 1523491200}},
                                                      {"entities": {"$exists": True}},
                                                      {"keywords": {"$exists": True}}
                                                  ]},
                                                  projection={"text": 1, "entities": 1, "keywords": 1},
                                                  limit=2000,
                                                  sort=True, sort_field="retweet_count")

        for tweet in tweets:
            if len(tweet['entities']) > 2 and len(tweet['keywords']) > 2:
                tweet_list.append(tweet['text'])

        data_list = list(self.chunks(tweet_list, 10))  # Chunk data
        for data in data_list:
            if len(data) == 10:
                crowd_data.append({
                    "tweet_list": data
                })

        job.upload(data=crowd_data, force=True)

    def process_job(self):
        data_list = []
        job = self.client.get_job(1256982)
        tweets = self.db_connection.find_document(collection=DB.TWEET_COLLECTION,
                                                  filter={"$and": [
                                                      {"created_at_epoch": {"$gt": 1520812800}},
                                                      {"created_at_epoch": {"$lt": 1523491200}},
                                                      {"entities": {"$exists": True}},
                                                      {"keywords": {"$exists": True}}
                                                 ]},
                                                  projection={"text": 1, "entities": 1, "keywords": 1})

        for tweet in tweets:
            if len(tweet['entities']) > 2 and len(tweet['keywords']) > 2:
                entities = []
                for entity_data in tweet['entities']:
                    if entity_data['entity'] not in entities:
                        entities.append(entity_data['entity'])

                data_list.append({
                    "tweet_content": tweet["text"],
                    "entity_list": entities,
                    "keyword_list": tweet["keywords"],
                    "full_list": entities + tweet["keywords"]
                })

        job.upload(data=data_list, force=True)

    def update_data(self, tweet_content, entity_list):
        job = self.client.get_job(1239688)
        data_list = []
        entity_amount = 0
        data = {
            CF.TWEET_CONTENT: tweet_content,
            "entity_list": entity_list
        }
        for index, entity in enumerate(entity_list):
            entity_no = index + 1
            data['entity%s' % entity_no] = entity
            data['dropdown%s' % entity_no] = entity
            entity_amount += 1

        data[CF.ENTITY_AMOUNT] = entity_amount

        if len(entity_list) < 10:
            # empty_entities = 10 - len(entity_list)
            for i in range(len(entity_list) + 1, 11):
                data['entity%s' % i] = ""

        data_list.append(data)

        job.upload(data=data_list, force=True)

cf = CrowdFlower()
# cf.process_job()
# cf.get_judgements(job_id=1256982)
cf.get_fact_opinion(job_id=1257130)

