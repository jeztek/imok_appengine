import tweepy
import logging

def twitter_post(user, message):
  if not user.twitter_username or not user.twitter_password:
    return False

  basic_auth = tweepy.BasicAuthHandler(user.twitter_username, user.twitter_password)

  api = tweepy.API(basic_auth)
  update = api.update_status(message)
  print update.text
  return True

def validate_password(username, password):
  basic_auth = tweepy.BasicAuthHandler(username, password)

  api = tweepy.API(basic_auth)
  return api.verify_credentials()