import crowdflower.client
import os
from db_engine import DBConnection
import json
from cons import CROWDFLOWER as CF
from cons import DB, TWEET
import requests
import json
from watson_developer_cloud import NaturalLanguageUnderstandingV1
from watson_developer_cloud.natural_language_understanding_v1 import Features, SentimentOptions, RelationsOptions, SemanticRolesVerb


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
        self.nlu = NaturalLanguageUnderstandingV1(version='2017-02-27',
                                                  username="b90a4616-36a2-447a-941f-256419b8f3e4",
                                                  password="t0BCpLI8fzSA")

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
        index_resolver = {
            "tweet1": 0,
            "tweet2": 1,
            "tweet3": 2,
            "tweet4": 3,
            "tweet5": 4,
            "tweet6": 5,
            "tweet7": 6,
            "tweet8": 7,
            "tweet9": 8,
            "tweet10": 9
        }
        results = self.judgements_session.get(
            url="https://api.figure-eight.com/v1/jobs/%s/judgments.json?key=%s&page=%s" %
                (job_id, self.api_key, page_no))

        content = json.loads(results.content)
        no_count = 0
        yes_count = 0
        for key, result in content.iteritems():
            answers = result[CF.FACTCHECKABLE_ANSWERS]
            answers = answers['res']
            tweets_to_check = {}
            for answer in answers:
                if len(answer) != 10:
                    for tweet in answer:
                        if tweet not in tweets_to_check:
                            tweets_to_check[tweet] = 1

                        else:
                            tweets_to_check[tweet] = tweets_to_check[tweet] + 1

            tweet_list = result[CF.TWEET_LIST]

            for tweet, occurrence in tweets_to_check.iteritems():
                text = tweet_list[index_resolver.get(tweet)]
                if occurrence > 1:
                    yes_count += 1
                    # text = tweet_list[index_resolver.get(tweet)]
                    # self.db_connection.find_and_update(collection=DB.RELEVANT_TWEET_COLLECTION,
                    #                                    query={"text": text, TWEET.SET_TO_FACTCHECK: {"$exists": False}},
                    #                                    update={"$set": {TWEET.SET_TO_FACTCHECK: True}})

                else:
                    self.db_connection.find_and_update(collection=DB.RELEVANT_TWEET_COLLECTION,
                                                       query={"text": text, TWEET.SET_TO_FACTCHECK: {"$exists": False}},
                                                       update={"$set": {TWEET.SET_TO_FACTCHECK: False}})

        print yes_count
        print no_count




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

    def fact_checking_processing(self, job_id):
        data_list = []
        job = self.client.get_job(job_id)
        # tweets = self.db_connection.find_document(collection=DB.RELEVANT_TWEET_COLLECTION,
        #                                           filter={"$and":[{TWEET.SET_TO_FACTCHECK: True},
        #                                                           {"crowdsourced":{"$exists": False}}]},
        #                                           projection={TWEET.TEXT: 1})

        tweets = list(self.db_connection.get_random_sample(collection=DB.RELEVANT_TWEET_COLLECTION,
                                                      query={"$and":[{"set_to_factcheck": True},
                                                                     {"crowdsourced":{"$exists": False}}]}, size=300))

        bulk_op = self.db_connection.start_bulk_upsert(collection=DB.RELEVANT_TWEET_COLLECTION)
        # print tweets.count()
        for tweet in tweets:
            data_list.append({"tweet": tweet["text"]})
            self.db_connection.add_to_bulk_upsert(query={"_id": tweet["_id"]},
                                                  data={"crowdsourced": True}, bulk_op=bulk_op)

        self.db_connection.end_bulk_upsert(bulk_op=bulk_op)

        job.upload(data=data_list, force=True)

    def get_old_judgements(self, job_id):
        page_no = 1
        crowd_results = {}
        results = self.judgements_session.get(
            url="https://api.figure-eight.com/v1/jobs/%s/judgments.json?key=%s&page=%s" %
                (job_id, self.api_key, page_no))

        content = json.loads(results.content)
        for key, result in content.iteritems():
            crowd_results[result['tweet_content']] = {"first_entity": result["please_indicate_the_first_entity_of_your_link_note_this_must_be_different_from_the_second_entity"]["res"],
                                                "second_entity": result["please_indicate_the_second_entity_of_your_link_note_this_must_be_different_from_the_first_entity"]["res"],
                                                "simple_relation": result["what_is_the_simple_link_between_the_entities_you_have_chosen"],
                                                "entity_list": result["entity_list"]
                                                }

        total_tp = 0
        total_fn = 0
        correct_relations = 0
        incorrect_relations = 0
        wrong_instructions = 0
        for key, value in crowd_results.iteritems():
            print key
            print "---------------------------------------"
            print "entity list: %s" % value["entity_list"]
            print "first_entities: %s" % value['first_entity']
            print "Second entities: %s" % value['second_entity']
            print "Simple relation: %s" % value['simple_relation']
            print "---------------------------------------"
            tp = int(raw_input("tp?\n"))
            total_tp += tp
            fn = int(raw_input("fn?\n"))
            total_fn += fn
            corr_r = int(raw_input("correct relations (small verb ?\n"))
            correct_relations += corr_r
            incc_r = int(raw_input("incorrect relations (small verb) ?\n"))
            incorrect_relations += incc_r
            wrong_ins = int(raw_input("wrong instructions (long phrase) ?\n"))
            wrong_instructions += wrong_ins
            print "---------------------------------------\n\n\n\n\n\n\n\n\n\n\n"

        print "tp: %d" % total_tp
        print "fn: %d" % total_fn
        print "correct relations: %d" % correct_relations
        print "incorrect relations: %d" % incorrect_relations
        print "wrong instructions: %d" % wrong_instructions

    def check_relations(self, job_id):
        page_no = 1
        tweet_list = []
        results = self.judgements_session.get(
            url="https://api.figure-eight.com/v1/jobs/%s/judgments.json?key=%s&page=%s" %
                (job_id, self.api_key, page_no))

        content = json.loads(results.content)
        for key, result in content.iteritems():
            tweet_list.append(result['tweet_content'])


        total_relations = len(tweet_list)
        valid_relations = 0
        for tweet in tweet_list:
            relations = self.nlu.analyze(text=tweet, features=Features(semantic_roles=SemanticRolesVerb()))
            print tweet
            semantic_roles = relations["semantic_roles"]
            for entry in semantic_roles:
                print "subject: %s" % entry["subject"]["text"]
                print "verb: %s" % entry["action"]["text"]
                if "object" in entry:
                    print "object: %s" % entry["object"]["text"]
                print "------------------------------------------"
                valid = raw_input("valid?\n")
                if valid == "y":
                    valid_relations += 1


        print valid_relations

    def get_factchecking_judgements(self, job_id):
        index_resolver = {
            'almost_definitely_true': 1,
            'likely_to_be_false': 0,
            'almost_definitely_false': 0,
            'very_ambiguous__i_really_cant_decide': -1
        }

        page_no = 2
        results = self.judgements_session.get(
            url="https://api.figure-eight.com/v1/jobs/%s/judgments.json?key=%s&page=%s" %
                (job_id, self.api_key, page_no))

        content = json.loads(results.content)
        for key, result in content.iteritems():
            almost_definitely_true_count = 0
            likely_to_be_false_count = 0
            almost_definitely_false_count = 0
            ambiguous_count = 0
            source_list = []
            author_list = []

            tweet = result['tweet']
            evidence = result['evidence']['res']
            source_list = result['source']
            author_list = result['author']
            aggregate_rating = index_resolver.get(result['rating']['agg'])
            for value in result['rating']['res']:
                if value == 'almost_definitely_true':
                    almost_definitely_true_count += 1

                elif value == 'likely_to_be_false':
                    likely_to_be_false_count += 1

                elif value == 'almost_definitely_false':
                    almost_definitely_false_count += 1

                elif value == 'very_ambiguous__i_really_cant_decide':
                    ambiguous_count += 1

            doc = {
                TWEET.ALMOST_DEFINITELY_TRUE_COUNT: almost_definitely_true_count,
                TWEET.LIKELY_TO_BE_FALSE_COUNT: likely_to_be_false_count,
                TWEET.ALMOST_DEFINITELY_FALSE_COUNT: almost_definitely_false_count,
                TWEET.AMBIGUOUS_COUNT: ambiguous_count,
                TWEET.AGGREGATE_LABEL: aggregate_rating,
                TWEET.TOTAL_CROWDSOURCING_COUNT: almost_definitely_true_count + likely_to_be_false_count + almost_definitely_false_count + ambiguous_count,
                TWEET.EVIDENCE: evidence,
                TWEET.CROWDSOURCING_SOURCE_LIST: source_list,
                TWEET.CROWDSOURCING_AUTHOR_LIST: author_list
            }

            self.db_connection.find_and_update(collection=DB.RELEVANT_TWEET_COLLECTION, query={"text": tweet},
                                               update={"$set": doc})

    def evaluate_interesting_statements(self, job_id):
        # index_resolver = {
        #     "tweet1": res
        # }
        page_no = 1
        tp = 0
        tn = 0
        fp = 0
        fn = 0
        results = self.judgements_session.get(
            url="https://api.figure-eight.com/v1/jobs/%s/judgments.json?key=%s&page=%s" %
                (job_id, self.api_key, page_no))

        content = json.loads(results.content)
        for key, result in content.iteritems():
            for tweet in result['tweet_list']:
                print tweet


            # for value in result["tick_the_box_of_the_tweets_that_are_politically_important_andor_worth_factchecking"]["res"]:


    def index_resolver(self, list_to_check, value):
        resolver = {
            "tweet1": list_to_check[0],
            "tweet2": list_to_check[1],
            "tweet3": list_to_check[2],
            "tweet4": list_to_check[3],
            "tweet5": list_to_check[4],
            "tweet6": list_to_check[5],
            "tweet7": list_to_check[6],
            "tweet8": list_to_check[7],
            "tweet9": list_to_check[8],
            "tweet10": list_to_check[9],
        }

        return resolver.get(value)








cf = CrowdFlower()
# cf.process_job()
# cf.get_judgements(job_id=1257130)
# cf.fact_checking_processing(1260770)
# cf.get_old_judgements(job_id=1256982)
# cf.check_relations(job_id=1256982)
# cf.fact_checking_processing(job_id=1260144)
# cf.get_fact_opinion(job_id=1257130)
# cf.get_factchecking_judgements(job_id=1260770)
cf.evaluate_interesting_statements(job_id=1257130)