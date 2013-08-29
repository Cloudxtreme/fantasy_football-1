var players = {};
var leagues = {};

if (!window.console || console === "undefined") {
    var console = { log: function (logMsg) { } };
}

var o_body_1_template = "<tr class='o_player_row' id={{player_key}}>" +
    "<td class='row_name'>{{name}}</td>" +
    "<td class='row_team'>{{team_abbr}}</td>" +
    "<td class='row_pos'>{{eligible_positions}}</td>" +
    "</tr>";

var o_body_2_template = "<tr class='o_player_row' id={{player_key}}>" +
    "<td class='row_4'>{{stats.4.value}}</td>" +
    "<td class='row_5'>{{stats.5.value}}</td>" +
    "<td class='row_9'>{{stats.9.value}}</td>" +
    "<td class='row_10'>{{stats.10.value}}</td>" +
    "<td class='row_12'>{{stats.12.value}}</td>" +
    "<td class='row_13'>{{stats.13.value}}</td>" +
    "</tr>";

var o_body_3_template = "<tr class='o_player_row' id={{player_key}}>" +
    "<td class='row_6'>{{stats.6.value}}</td>" +
    "<td class='row_18'>{{stats.18.value}}</td>" +
    "</tr>";

var o_body_4_template = "<tr class='o_player_row' id={{player_key}}>" +
    "<td class='row_15'>{{stats.15.value}}</td>" +
    "<td class='row_16'>{{stats.16.value}}</td>" +
    "<td class='row_57'>{{stats.57.value}}</td>" +
    "</tr>";

var k_body_1_template = "<tr class='k_player_row' id={{player_key}}>" +
    "<td class='row_name'>{{name}}</td>" +
    "<td class='row_team'>{{team_abbr}}</td>" +
    "<td class='row_pos'>{{eligible_positions}}</td>" +
    "</tr>";

var k_body_2_template = "<tr class='k_player_row' id={{player_key}}>" +
    "<td class='row_29'>{{stats.29.value}}</td>" +
    "<td class='row_19'>{{stats.19.value}}</td>" +
    "<td class='row_20'>{{stats.20.value}}</td>" +
    "<td class='row_21'>{{stats.21.value}}</td>" +
    "<td class='row_22'>{{stats.22.value}}</td>" +
    "<td class='row_23'>{{stats.23.value}}</td>" +
    "</tr>";

var league_template = '<div class="league">\
    <h2><a href="{{url}}">{{name}}</a></h2>\
    <div class="row player_row">\
        <h3>Offensive Players</h3>\
        <div class="col-lg-3 col-md-3 col-sm-4 col-xs-1">\
            <table class="table table-condensed table-striped player_table" id="o_table_{{league_id}}_1">\
                <thead>\
                    <th>Name</th>\
                    <th>Team</th>\
                    <th>Pos</th>\
                </thead>\
                <tbody id="o_table_body_{{league_id}}_1"></tbody>\
            </table>\
        </div>\
        <div class="col-lg-6 col-md-6 col-sm-4 col-xs-1">\
            <table class="table table-condensed table-striped player_table" id="o_table_{{league_id}}_2">\
                <thead>\
                    <th>Pass Yds</th>\
                    <th>Pass TDs</th>\
                    <th>Rush Yds</th>\
                    <th>Rush TDs</th>\
                    <th>Rec Yds</th>\
                    <th>Rec TDs</th>\
                </thead>\
                <tbody id="o_table_body_{{league_id}}_2"></tbody>\
            </table>\
        </div>\
        <div class="col-lg-1 col-md-1">\
            <table class="table table-condensed table-striped player_table hidden-sm hidden-xs" id="o_table_{{league_id}}_3">\
                <thead>\
                    <th>Int</th>\
                    <th>Fum</th>\
                </thead>\
                <tbody id="o_table_body_{{league_id}}_3"></tbody>\
            </table>\
        </div>\
        <div class="col-lg-2 col-md-2 hidden-sm hidden-xs">\
            <table class="table table-condensed table-striped player_table hidden-sm hidden-xs" id="o_table_{{league_id}}_4">\
                <thead>\
                    <th>Ret TD</th>\
                    <th>2pt</th>\
                    <th>Fum</th>\
                </thead>\
                <tbody id="o_table_body_{{league_id}}_4"></tbody>\
            </table>\
        </div>\
    </div>\
    <div class="row player_row">\
        <h3>Kickers</h3>\
        <div class="col-lg-3">\
            <table class="table table-condensed player_table" id="k_table_{{league_id}}_1">\
                <thead>\
                    <th>Name</th>\
                    <th>Team</th>\
                    <th>Pos</th>\
                <thead>\
                <tbody id="k_table_body_{{league_id}}_1"></tbody>\
            </table>\
        </div>\
        <div class="col-lg-9">\
            <table class="table table-condensed player_table" id="k_table_{{league_id}}_2">\
                <thead>\
                    <th>PAT</th>\
                    <th>0-19</th>\
                    <th>20-29</th>\
                    <th>30-39</th>\
                    <th>40-49</th>\
                    <th>50+</th>\
                </thead>\
                <tbody id="k_table_body_{{league_id}}_2"></tbody>\
            </table>\
        </div>\
    </div>\
</div>';

function Stat(stat_dict) {
    "use strict";
    this.id = stat_dict.id;
    this.player = stat_dict.player;
    this.season = stat_dict.season;
    this.stat_id = stat_dict.stat_id;
    this.value = stat_dict.value;
    this.week = stat_dict.week;
}

function Player(player_dict, league_id) {
    "use strict";
    var s, stat, html;
    this.bye_week = player_dict.bye_week;
    this.display_position = player_dict.display_position;
    this.editorial_player_key = player_dict.editorial_player_key;
    this.editorial_team_full_name = player_dict.editorial_team_full_name;
    this.editorial_team_key = player_dict.editorial_team_key;
    this.eligible_positions = player_dict.eligible_positions;
    this.headshot_url = player_dict.headshot_url;
    this.image_url = player_dict.image_url;
    this.is_undroppable = player_dict.is_undroppable;
    this.name = player_dict.name;
    this.player_id = player_dict.player_id;
    this.player_key = player_dict.player_key;
    this.position_type = player_dict.position_type;
    this.times_updates = player_dict.times_updates;
    this.uniform_number = player_dict.uniform_number;
    this.team_abbr = player_dict.team_abbr;
    this.league_id = league_id;
    this.stats = [];
    for (s in player_dict.stats) {
        stat = new Stat(player_dict.stats[s]);
        this.stats[s] = stat;
    }
    this.render = function render() {
        var s, stat;

        if (this.position_type === "O") {
            html = Mustache.render(o_body_1_template, this);
            console.log("stats", this.stats);
            $("#o_table_" + this.league_id + "_1").append(html);
            console.log("table", "#o_table_" + this.league_id + "_1");
            html = Mustache.render(o_body_2_template, this);
            $("#o_table_" + this.league_id + "_2").append(html);
            html = Mustache.render(o_body_3_template, this);
            $("#o_table_" + this.league_id + "_3").append(html);
            html = Mustache.render(o_body_4_template, this);
            $("#o_table_" + this.league_id + "_4").append(html);
        } else if (this.position_type === "K") {
            html = Mustache.render(k_body_1_template, this);
            $("#k_table_" + this.league_id + "_1").append(html);
            html = Mustache.render(k_body_2_template, this);
            $("#k_table_" + this.league_id + "_2").append(html);
        }

    };
}
function League(league_dict) {
    "use strict";
    var p, player;
    console.log('league dict', league_dict);
    this.name = league_dict.name;
    this.id = league_dict.id;
    this.record = league_dict.record;
    this.url = league_dict.url;
    this.league_type = league_dict.league_type;
    this.league_id = this.id;
    this.players = [];
    console.log("league players", league_dict.players);
    for (p in league_dict.players) {
        player = new Player(league_dict.players[p], this.id);
        this.players.push(player);
    }
    console.log("this players", this.players);

    this.render = function render() {
        var html, rows, p, player;
        rows = [];
        console.log('start render', this.players);
        // Add the league template to the document.
        html = Mustache.render(league_template, this);
        $("#leagues").append(html);

        console.log("players", this.players);
        for (p in this.players) {
            player = this.players[p];
            console.log('league player', player);
            player.render();
        }

    };

}


function update_player(player) {
    "use strict";
    var s, existing_stat, current_stat, existing_player;
    existing_player = players[player.player_key];
    for (s in player.stats) {
        existing_stat = player.stats[s];
        current_stat = player.stats[s];
        console.log("existing", player.stats[s], "curr", player.stats[s], "s", s);
        if (current_stat > existing_stat) {
            $("#" + player.player_key).find("#row_" + s).html(player.stats[s].value);
            $("#" + player.player_key).find("#row_" + s).highlight();
        } else if (current_stat < existing_stat) {
            $("#" + player.player_key).find("#row_" + s).html(player.stats[s].value);
            $("#" + player.player_key).find("#row_" + s).highlight();
        } else {
            console.log($("#" + player.player_key).find("#row_" + s));
            $("#" + player.player_key).find("#row_" + s).highlight();
        }
    }
}

function add_player(responseText, statusText, xhr, $form) {
    "use strict";
    var p, player;
    console.log('responsetext', responseText);
    for (p in responseText) {
        console.log(p);
        player = responseText[p];
        // Check if player already is on the list. If so, we're doing an update.
        if (player.player_key in players) {
            update_player(player);
        } else {
            // Add to the player list for future updates.
            players[player.player_key] = player;
            player.render();
        }

    }

}
function new_player_form() {
    "use strict";
    var options = {
        success :       add_player,  // post-submit callback
        dataType:      'json',
        timeout:       3000
        // other available options:
        //url =       url         // override for form's 'action' attribute
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

function display_leagues(responseText) {
    "use strict";
    var l, league;
    console.log('display');
    for (l in responseText) {
        league = new League(responseText[l]);
        console.log(league);
        leagues[league.id] = league;
        league.render();
        console.log('rendered');
    }
}
function get_leagues() {
    "use strict";
    $.ajax({
        url: '/api/leagues/',
        success: function (responseText, statusText, xhr, $form) {
            display_leagues(responseText);
        }
//        dataType: 'json'
//        data:
    });
}

function get_stats() {
    "use strict";
    $.ajax({
        url: '/api/scores/',
        success: function (responseText, statusText, xhr, $form) {
            add_player(responseText);
        }
//        dataType: 'json'
//        data:
    });
}

$(document).ready(function () {
    "use strict";
//    new_player_form();
    get_leagues();
});