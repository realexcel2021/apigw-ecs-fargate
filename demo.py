import json
import logging
import os
import time
import uuid
from datetime import datetime
import requests
import boto3
from botocore.exceptions import BotoCoreError, ClientError
from intent_classifier import LegalIntentClassifier
from intent_handler import (
    handle_knowledge_base,
    handle_fallback,
    handle_greeting,
    handle_done
)

from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)

# Environment variables
APPSYNC_API_URL = os.environ['APPSYNC_API_URL']
APPSYNC_API_KEY = os.environ['APPSYNC_API_KEY']


# GraphQL mutation for creating a message
create_message_mutation = """
mutation CreateMessage($input: CreateMessageInput!) {
  createMessage(input: $input) {
    id
    conversationId
    userId
    isBot
    content
    supportingContent
    citations
    explanation
    timestamp
  }
}
"""

# GraphQL mutation for creating a conversation
create_conversation_mutation = """
mutation CreateConversation($input: CreateConversationInput!) {
  createConversation(input: $input) {
    id
    createdAt
    summary
    title
    userId
  }
}
"""


def save_message_to_appsync(message):
    # Ensure all necessary fields are present
    # 'supportingContent' and 'explanation' are not required
    if not all(key in message for key in ['conversationId', 'userId', 'content', 'citations']):
        logging.error("Missing required fields in message.")
        return {
            'statusCode': 400,
            'body': json.dumps({'error': 'Missing required fields'})
        }

    payload = {
        'query': create_message_mutation,
        'variables': {
            'input': message
        }
    }

    headers = {
        'Content-Type': 'application/json',
        'x-api-key': APPSYNC_API_KEY
    }

    logging.info(f"Sending payload to AppSync: {payload}")

    try:
        response = requests.post(APPSYNC_API_URL, json=payload, headers=headers)
        response_data = response.json()

        if 'errors' in response_data:
            logging.error(f"GraphQL errors: {response_data['errors']}")
            return {
                'statusCode': 500,
                'body': json.dumps({'error': response_data['errors']})
            }

        logging.info(f"Message saved successfully: {response_data['data']['createMessage']}")
        print(f"Message saved successfully: {response_data['data']['createMessage']}")
        return {
            'statusCode': 200,
            'body': json.dumps(response_data['data']['createMessage'])
        }
    except requests.exceptions.RequestException as e:
        logging.error(f"HTTP request failed: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }


def save_conversation_to_appsync(user_id, timestamp):
    # Define the input for creating a new conversation
    conversation_input = {
        'createdAt': timestamp,  # Example, replace with the current timestamp
        'summary': '',
        'title': f"Conversation at {timestamp}",
        'userId': user_id
    }

    payload = {
        'query': create_conversation_mutation,
        'variables': {
            'input': conversation_input
        }
    }

    headers = {
        'Content-Type': 'application/json',
        'x-api-key': APPSYNC_API_KEY
    }

    logging.info(f"Sending payload to AppSync to create conversation: {payload}")

    try:
        response = requests.post(APPSYNC_API_URL, json=payload, headers=headers)
        response_data = response.json()

        if 'errors' in response_data:
            logging.error(f"GraphQL errors: {response_data['errors']}")
            return None

        logging.info(f"Conversation created successfully: {response_data['data']['createConversation']}")
        return response_data['data']['createConversation']['id']
    except requests.exceptions.RequestException as e:
        logging.error(f"HTTP request failed: {e}")
        return None


def classify_intent(query):
    try:
        classifier = LegalIntentClassifier()
        intent = classifier.predict_intent(query)
        logging.info(f"Classified intent for query '{query}' as '{intent}'")
        return intent
    except Exception as e:
        logging.error(f"Failed to classify intent. Exception: {str(e)}")
        return "knowledge_base"  # Default to knowledge_base on error


def handle_intent(intent, query):
    try:
        if intent == "knowledge_base":
            response = handle_knowledge_base(query)
        elif intent == "greeting":
            response = handle_greeting(query)
        elif intent == "done":
            response = handle_done(query)
        else:
            response = handle_fallback(query)
        logging.info(f"Intent: {intent}, Query: {query}, Response: {response}")
        return response
    except Exception as e:
        logging.error(f"Failed to handle intent. Exception: {str(e)}")
        return "I'm sorry, I encountered an error processing your request. Please try again with a legal-related question."


def lambda_handler(event, context):
    results = []
    try:
        for record in event['Records']:
            message_body = json.loads(record['body'])

            # Ensure the expected structure of the message
            if 'content' not in message_body or 'query' not in message_body['content']:
                logging.error("Missing 'content' or 'query' key in event")
                continue

            # Extract the message details from the parsed body
            user_id = message_body.get('userId', '')
            print("user_id", user_id)
            query = message_body['content']['query']
            timestamp = message_body.get('timestamp', '')

            logging.info(f"Processing message from user '{user_id}' with query '{query}'")
            conversationId = message_body.get('conversationId', '')
            if conversationId is None or conversationId == '':
                # Create a new conversation record using GraphQL mutation for the userId
                conversationId = save_conversation_to_appsync(user_id, timestamp)
                if conversationId is None:
                    logging.error("Failed to create a new conversation")
                    continue

            # Prepare message to save to AppSync
            user_query = {
                'conversationId': conversationId,
                'userId': user_id,
                'isBot': False,
                'content': json.dumps(message_body['content']),  # Ensure it's valid JSON
                'supportingContent': json.dumps(message_body.get('supportingContent', '{}')),  # Ensure it's valid JSON
                'timestamp': timestamp,  # Include the timestamp
                'citations': json.dumps({})
            }

            # Classify intent
            intent = classify_intent(query)

            # Handle intent and trigger sub-function
            response = handle_intent(intent, query)

            # If the response is a dict (which includes citations), extract text and citations
            if isinstance(response, dict):
                response_text = response.get('text', '')
                response_citations = response.get('citations', {})
            else:
                response_text = response
                response_citations = {}

            # Save message to AppSync
            logging.debug(f"Saving user_query: {user_query}.")
            appsync_response = save_message_to_appsync(user_query)
            logging.debug(f"appsync_response (user_query): {appsync_response}.")

            # timestamp = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
            ai_response = {
                'conversationId': conversationId,
                'userId': user_id,
                'isBot': True,
                'content': json.dumps({'response': response_text}),
                'citations': json.dumps(response_citations),  # Ensure it's valid JSON
                'supportingContent': json.dumps(message_body.get('supportingContent', '{}')),
                # 'explanation': message_body.get('explanation', ''),
                'timestamp': timestamp,  # Include the timestamp
            }

            # Save message to AppSync
            logging.debug(f"Saving ai_response: {ai_response}.")
            appsync_response = save_message_to_appsync(ai_response)
            logging.debug(f"appsync_response(ai_response): {appsync_response}.")
            results.append(appsync_response)

        return {
            'statusCode': 200,
            'body': json.dumps(results)
        }
    except Exception as e:
        logging.error(f"An error occurred: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps(f'Error: {str(e)}')
        }