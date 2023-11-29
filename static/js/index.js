try {
  Typekit.load({ async: true });
} catch (e) {
  console.error(e);
}

// on fullname input change
$("#fullname").change(function () {
  var fullname = $("#fullname").val();

  if ($.trim(fullname) == "") {
    return false;
  }

  $.ajax({
    url: "/user/update",
    type: "POST",
    headers: { "X-CSRFToken": "{{ csrf_token }}" },
    data: { fullname: fullname },

    success: function (response) {
      // update placeholder
      $("#fullname").attr("placeholder", fullname);
      $("#user-fullname").html(fullname);
    },
    error: function (error) {
      console.log(error);
    },
  });
});

$(".expand-button").click(function () {
  $("#profile").toggleClass("expanded");
  $("#contacts").toggleClass("expanded");
});

// search bots
$("#botname").on("keyup", function () {
  var value = $(this).val().toLowerCase();
  $("#contacts li").filter(function () {
    $(this).toggle($(this).text().toLowerCase().indexOf(value) > -1);
  });
});

// active (background) bot on click
$(".contact").click(function () {
  $(".contact").removeClass("active");
  $(this).addClass("active");
});

// show menu dropdown
$("#menu").click(function () {
  $("#menu-dropdown").toggleClass("active");
});

// hide menu dropdown on click outside
$(document).mouseup(function (e) {
  if (!$("#menu").is(e.target)) {
    var container = $("#menu-dropdown");

    if (!container.is(e.target) && container.has(e.target).length === 0) {
      container.removeClass("active");
    }
  }
});

function newMessage() {
  let message = $(".message-textarea textarea").val();
  if ($.trim(message) == "") {
    return false;
  }

  $(
    '<li class="sent"><p>' +
      message.replace(/(?:\r\n|\r|\n)/g, "<br>") +
      "</p></li>" +
      `
      <p class="send-time">
      ${new Date().toLocaleTimeString("en-US", {
        hour: "numeric",
        minute: "numeric",
        hour12: true,
      })}
      </p>
      `
  ).appendTo($(".messages ul"));

  resetTextarea();

  // disable send button and textarea
  $(".submit").prop("disabled", true);
  $(".message-textarea textarea").prop("disabled", true);

  let message_data = {
    message: message,
    sender_type: "USER",
    time: new Date().toLocaleTimeString("en-US", {
      hour: "numeric",
      minute: "numeric",
      hour12: true,
    }),
  };

  setContactInfo(message_data);
  // sort contacts list
  sortContacts(conversation_id);
  scrollToBottom();

  $.ajax({
    url: "/conversation/" + conversation_id,
    type: "POST",
    headers: { "X-CSRFToken": "{{ csrf_token }}" },
    data: { message: message },

    success: function (response) {
      let conversation = response.data.conversation;
      message = response.data.message;
      setMessage(message, conversation.user_id);
      scrollToBottom();
    },
    error: function (error) {
      console.log(error);
    },
    complete: function () {
      // enable send button and textarea
      $(".submit").prop("disabled", false);
      $(".message-textarea textarea").prop("disabled", false);

      // focus on textarea
      $(".message-textarea textarea").focus();
    },
  });
}

$(".submit").click(function () {
  newMessage();
});

$(".message-textarea textarea").on("keydown", function (e) {
  // if shift + enter, add new line
  if (e.which == 13 && e.shiftKey) {
    // increase height of textarea if needed
    var height = $(".message-textarea textarea").height();
    if (height <= 50) {
      $(".message-textarea textarea").css("height", "+=10");
    }
    return true;
  }
  // if backspace, decrease height of textarea if needed
  else if (e.which == 8 && $(this).val() == "") {
    var height = $(".message-textarea textarea").height();
    if (height > 19) {
      $(".message-textarea textarea").css("height", "-=10");
    }
    return true;
  }
  // if enter, send message
  else if (e.which == 13) {
    newMessage();
    return false;
  }
});

let conversation_id = null;

function setConversation(conversation) {
  conversation_id = conversation.id;

  $("#chat-user").html(conversation.bot.name);
  $("#chat-description").html(conversation.bot.description);
}

function toggleStar(star, message_id) {
  $.ajax({
    url: "/feedback/" + message_id,
    type: "POST",
    data: { feedback: star },
    headers: { "X-CSRFToken": "{{ csrf_token }}" },
    success: function (response) {
      for (let i = 1; i <= 5; i++) {
        if (i <= star) {
          $(`#star-${i}-${message_id}`).addClass("active");
        } else {
          $(`#star-${i}-${message_id}`).removeClass("active");
        }
      }
    },
    error: function (error) {
      console.log(error);
    },
  });
}

function setMessage(message, user_id) {
  // Adjust message
  if (message.sender_type == "BOT" || message.sender_id != user_id) {
    let feedback = "";
    for (let i = 1; i <= 5; i++) {
      feedback += `
        <i 
          class="${i <= message.feedback ? "fa fa-star active" : "fa fa-star"}"
          aria-hidden="true" 
          id="star-${i}-${message.id}" 
          onclick="toggleStar(${i}, ${message.id})"
        ></i>`;
    }

    $(
      `<li class="replies">
          <p title="Copy to clipboard" onclick="copyToClipboard('${message.message.replace(
            /(?:\r\n|\r|\n)/g,
            "<br>"
          )}')">
          ${message.message.replace(/(?:\r\n|\r|\n)/g, "<br>")}
          <br><span title="Rate the response">${feedback}</span
          </p>
        </li>
        <p class="reply-time">
        ${message.time}
        </p>
      `
    ).appendTo($(".messages ul"));
  } else {
    $(
      `<li class="sent"><p>
          ${message.message.replace(/(?:\r\n|\r|\n)/g, "<br>")}
          </p></li>
          <p class="send-time">
          ${message.time}
          </p>
          `
    ).appendTo($(".messages ul"));
  }
  setContactInfo(message);
}

// $(".messages ul").on("click", ".replies p", function () {
function copyToClipboard(message) {
  message = message.replace(/<br>/g, "\n");

  navigator.clipboard.writeText(message).then(
    function () {
      console.log("Copied to clipboard successfully!");
    },
    function () {
      console.log("Unable to write to clipboard. :-(");
    }
  );
}

function viewConversation(conversation) {
  // chat-content display
  if (conversation_id == null) {
    $("#default-content").css("display", "none");
    $("#chat-content").css("display", "block");
  }

  if (conversation_id == conversation) {
    return;
  }

  // disable send button and textarea
  $(".submit").prop("disabled", true);
  $(".message-textarea textarea").prop("disabled", true);

  conversation_id = conversation;

  $.ajax({
    url: "/conversation/" + conversation,
    type: "GET",
    headers: { "X-CSRFToken": "{{ csrf_token }}" },
    success: function (response) {
      $(".messages ul").html("");
      let conversation = response.data.conversation;
      let messages = response.data.messages;

      setConversation(conversation);

      messages.forEach((message) => {
        setMessage(message, conversation.user_id);
      });
      scrollToBottom();
    },
    error: function (error) {
      console.log(error);
    },
    complete: function () {
      // enable send button and textarea
      $(".submit").prop("disabled", false);
      $(".message-textarea textarea").prop("disabled", false);

      // focus on textarea
      $(".message-textarea textarea").focus();
    },
  });
}

function scrollToBottom() {
  let height = parseInt($(".messages ul").css("height").slice(0, -2));

  if (height < $(document).height()) {
    $(".messages").animate({ scrollTop: $(document).height() }, "slow");
  } else {
    $(".messages").animate({ scrollTop: height }, "fast");
  }
}

function setContactInfo(message) {
  if (message.sender_type == "BOT") {
    $(".contact.active .preview").html(message.message);
  } else {
    $(".contact.active .preview").html("<span>You: </span>" + message.message);
  }

  $(".contact.active .preview").attr("title", message.message);
  $(".contact.active .time").html(message.time);
}

// bring contact to top of list
function sortContacts(id) {
  let contact = $(`.contact[id=${id}]`);

  // if contact is already at top of list, do nothing
  if (contact.prev().length > 0) {
    // animate contact show and hide
    contact.hide().show("fast");
    // prepend contact to top of list
    $("#contacts ul").prepend(contact);
  }
}

function resetContactInfo() {
  $(".contact.active .preview").html("No messages yet");
  $(".contact.active .preview").attr("title", "");
  $(".contact.active .time").html("");
}

function resetTextarea() {
  $(".message-textarea textarea").val(null);
  $(".message-textarea textarea").height(19);
}

function clearConversation() {
  $.ajax({
    url: "/clear_conversation/" + conversation_id,
    type: "GET",
    headers: { "X-CSRFToken": "{{ csrf_token }}" },
    success: function (response) {
      $(".messages ul").html("");
      resetContactInfo();
      resetTextarea();
    },
    error: function (error) {
      console.log(error);
    },
    complete: function () {
      // focus on textarea
      $(".message-textarea textarea").focus();
      $("#menu-dropdown").removeClass("active");
    },
  });
}

function saveConversation() {
  $("#menu-dropdown").removeClass("active");
  $.ajax({
    url: "/save_conversation/" + conversation_id,
    type: "GET",
    headers: { "X-CSRFToken": "{{ csrf_token }}" },
    success: function (response) {
      window.location.href = "/save_conversation/" + conversation_id;
    },
    error: function (error) {
      console.log(error);
    },
  });
}

$("#bot-name").on("change", function () {
  var botName = $("#bot-name").val();
  var botPrompt = $("#bot-prompt").val();

  if (botPrompt.includes("{bot name}")) {
    $("#bot-prompt").val(botPrompt.replace("{bot name}", botName));
  } else {
    botName = botName ? botName : "{bot name}";

    // replace using regex
    $("#bot-prompt").val(botPrompt.replace(/(?<=I'm ).*?(?=,)/, botName));
  }
});

$("#bot-description").on("change", function () {
  var botDescription = $("#bot-description").val();
  var botPrompt = $("#bot-prompt").val();

  if (botPrompt.includes("{bot description}")) {
    $("#bot-prompt").val(
      botPrompt.replace("{bot description}", botDescription)
    );
  } else {
    botDescription = botDescription ? botDescription : "{bot description}";
    // replace using regex
    $("#bot-prompt").val(
      botPrompt.replace(/(?<=, ).*?(?=\.)|(?<=, ).*?(?=\?)/, botDescription)
    );
  }
});
