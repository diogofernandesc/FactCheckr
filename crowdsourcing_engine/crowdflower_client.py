import crowdflower
import crowdflower.client
import os
import json
from cons import CROWDFLOWER as CF


def dumper(obj):
    try:
        return obj.toJSON()
    except:
        return obj.__dict__


class CrowdFlower(object):

    def __init__(self):
        self.client = crowdflower.client.Client(os.getenv("CROWDFLOWER_API_KEY"))
        # self.connection = crowdflower.Connection(api_key=os.getenv("CROWDFLOWER_API_KEY"))

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

    def process_job(self):
        job = self.client.get_job(1239672)
        data = {
            "tweet_content": "A given tweet"
        }
        job.upload(data=[data], force=True)

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
cf.process_job()
