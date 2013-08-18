var players = {};
function update_player(player) {
    existing_player = players[player.player_key];
    for (s in player.stats) {
        existing_stat = player.stats[s];
        current_stat = player.stats[s];
        console.log("existing", player.stats[s], "curr", player.stats[s], "s", s)
        if (current_stat > existing_stat) {
            $("#" + player.player_key).find("#row_" + s).html(player.stats[s].value);
            $("#" + player.player_key).find("#row_" + s).highlight();
        }
        else if (current_stat < existing_stat) {
            $("#" + player.player_key).find("#row_" + s).html(player.stats[s].value);
            $("#" + player.player_key).find("#row_" + s).highlight();
        }
        else {
            console.log($("#" + player.player_key).find("#row_" + s))
            $("#" + player.player_key).find("#row_" + s).highlight();
        }
    }
}
function o_player_template(player) {
    for (s in player.stats) {
        var stat = player.stats[s];
        console.log(stat)
        console.log("stats_"+s)
        player["stats_" + s] = stat.value;
    }
    console.log(player)
    var output = Mustache.render("" +
        "<tr class='o_player_row' id={{player_key}}>" +
        "<td class='row_name'>{{name}}</td>" +
        "<td class='row_team'>TEAM</td>" +
        "<td class='row_pos'>{{eligible_positions}}</td>" +
        "<td class='row_4'>{{stats_4}}</td>" +
        "<td class='row_5'>{{stats_5}}</td>" +
        "<td class='row_9'>{{stats_9}}</td>" +
        "<td class='row_10'>{{stats_10}}</td>" +
        "<td class='row_12'>{{stats_12}}</td>" +
        "<td class='row_13'>{{stats_13}}</td>" +
        "<td class='row_15'>{{stats_15}}</td>" +
        "<td class='row_16'>{{stats_16}}</td>" +
        "<td class='row_6'>{{stats_6}}</td>" +
        "<td class='row_18'>{{stats_18}}</td>" +
        "<td class='row_57'>{{stats_57}}</td>" +
        "</tr>", player);
    return output
}

function k_player_template(player) {

}

function add_player_to_table(player) {
    if (player.position_type == 'K') {
        row_html = k_player_template(player);
        $('#k_table_body').append(row_html);

    }
    else if (player.position_type == 'O') {
        row_html = o_player_template(player);
        $('#o_table_body').append(row_html);

    }

    console.log(row_html);
    console.log(player);
}

function add_player(responseText, statusText, xhr, $form) {
    console.log('responsetext', responseText)
    for (var p in responseText) {
        console.log(p)
        player = responseText[p];
        // Check if player already is on the list. If so, we're doing an update.
        if (player.player_key in players) {
            update_player(player);
        }
        else {
            // Add to the player list for future updates.
            players[player.player_key] = player;
            add_player_to_table(player)
        }

    }

}
function new_player_form() {
    var options = {
        success:       add_player,  // post-submit callback
        dataType:      'json',
        timeout:       3000
        // other available options:
        //url:       url         // override for form's 'action' attribute
        //type:      type        // 'get' or 'post', override for form's 'method' attribute
        //dataType:  null        // 'xml', 'script', or 'json' (expected server response type)
        //clearForm: true        // clear all form fields after successful submit
        //resetForm: true        // reset the form after successful submit

        // $.ajax options can be used here too, for example:
        //timeout:   3000
    };

    // bind form using 'ajaxForm'
    $('#add_player_form').ajaxForm(options);
}

function get_stats() {
    $.ajax({
        url: '/api/scores/',
        success: function(responseText, statusText, xhr, $form) {
            add_player(responseText);
        }
//        dataType: 'json'
//        data:
    });
}

$(document).ready(function() {
//    new_player_form();
    get_stats();
});