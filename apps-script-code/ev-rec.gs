CLOUD_RUN_URL="https://ev-rec-bot-service-e2xtzyc2wq-uc.a.run.app";

function callBotService(user_params) {
  // Use the OpenID token inside App Scripts
  const token = ScriptApp.getIdentityToken();
  var options = {
    'method' : 'get',
    'headers': {'Authorization': 'Bearer ' + token},
  };
  // user query
  params = '/chat/' + user_params[0] + '/' + user_params[1]
  // call the server
  // @app.route("/chat/<fuel>/<min_conventional_fuel_economy_combined>")
  return UrlFetchApp.fetch(CLOUD_RUN_URL + params, options);
  }

/**
 * Responds to a MESSAGE event in Google Chat.
 *
 * @param {Object} event the event object from Google Chat
 */
function onMessage(event) {
  const user_params = event.message.text.replace(' ', "%20").split(",")
  var response = callBotService(user_params)
  return { "text": response.getContentText()};
}

/**
 * Responds to an ADDED_TO_SPACE event in Google Chat.
 *
 * @param {Object} event the event object from Google Chat
 */
function onAddToSpace(event) {
  var message = "";

  if (event.space.singleUserBotDm) {
    message = "Thank you for adding me to a DM, " + event.user.displayName + "!" + "Please input your preferred fuel type and minimum fuel efficiency (number in MPG), separating by comma. I will recommend the most suitable models for you.";
  } else {
    message = "Thank you for adding me to " +
        (event.space.displayName ? event.space.displayName : "this chat." + "Please input your preferred fuel type and minimum fuel efficiency (number in MPG), separating by comma. I will recommend the most suitable models for you.");
  }

  if (event.message) {
    // Bot added through @mention.
    message = message + "Please input your preferred fuel type and minimum fuel efficiency (number in MPG), separating by comma. I will recommend the most suitable models for you.";
  }

  return { "text": message };
}

/**
 * Responds to a REMOVED_FROM_SPACE event in Google Chat.
 *
 * @param {Object} event the event object from Google Chat
 */
function onRemoveFromSpace(event) {
  console.info("Bot removed from ",
      (event.space.name ? event.space.name : "this chat"));
}

