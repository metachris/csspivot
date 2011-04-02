/* Author: 

*/


var previewWindow;    
function preview(showdialog) {
    var form = document.createElement("form");
    form.setAttribute("method", "post");
    form.setAttribute("action", "/proxy");
    
    // setting form target to a window named 'formresult'
    form.setAttribute("target", "proxy");
    form.style.display = "none";
    
    var hiddenField = document.createElement("input");              
    hiddenField.setAttribute("name", "css");
    hiddenField.setAttribute("value", encodeURI($("#csspivot_css").val()));
    form.appendChild(hiddenField);

    var hiddenField = document.createElement("input");              
    hiddenField.setAttribute("name", "url");
    hiddenField.setAttribute("value", encodeURI($("#csspivot_url").val()));
    form.appendChild(hiddenField);

    var hiddenField = document.createElement("input");              
    hiddenField.setAttribute("name", "comment");
    hiddenField.setAttribute("value", encodeURI($("#csspivot_comment").val()));
    form.appendChild(hiddenField);

    if (!showdialog) {
        var hiddenField = document.createElement("input");              
        hiddenField.setAttribute("name", "s");
        hiddenField.setAttribute("value", "1");
        form.appendChild(hiddenField);
    }

    document.body.appendChild(form);
    form.submit();

    // if orig is shown, switch to preview
    if (is_orig_shown)
        pivot_toggleorig();
    
    /*
    if (!previewWindow || previewWindow.closed) {
        // opens a new window with the edit
        previewWindow = window.open("/preview", 'previewWindow',
        'left=20,top=20,width=800,height=600,toolbar=0,location=0,resizable=0,menubar=0,status=0');
    } else {
        previewWindow.focus();
    }
    */
}





var pivots_recent;

function get_recent_pivots() {
    if (pivots_recent) 
        return pivots_recent;

    recent = localStorage.getItem("pivots_recentlyviewed" + k);
    if (recent) {
        arr = recent.split(",");
        pivots_recent = arr;
        return pivots_recent;
    }
}

function showpivots(i) {
    // Show list of pivots for selected topic
    if (i == 4) {
        arr = get_recent_pivots();
        out = "";
        for (i in arr) {
            if (arr[i] != "") {
                //console.log(arr[i]);
                cnt = localStorage.getItem("pivots_recentlyviewed" + k + "_" + arr[i] + "_cnt");
                cnt_txt = "";
                if (cnt) { if (cnt > 0) cnt_txt = " &middot; " + cnt + " change"; if (cnt > 1) cnt_txt += "s"; }
                url = localStorage.getItem("pivots_recentlyviewed" + k + "_" + arr[i] + "_url");
                out += "<li><a href='/" + arr[i] + "' title='" + url + "'><code>" + arr[i] + "</code></a> &middot; <small>" + url + cnt_txt + "</small></li>";
            }
            if (i > 20) break;
        }
        $("#discover_pivotlist").html("<ul>" + out + "</ul>");
        $("#dialog_pivots").dialog("open");
        $("#dialog_pivots").dialog("option", "title", 'Recently Viewed'); 

    } else if (i == 0) {
        $("#discover_pivotlist").html($("#_recent").html());
        $("#dialog_pivots").dialog("open");
        $("#dialog_pivots").dialog("option", "title", 'New Pivots'); 

    } else if (i == 1) {
        $("#discover_pivotlist").html($("#_examples").html());
        $("#dialog_pivots").dialog("open");
        $("#dialog_pivots").dialog("option", "title", 'Selected Pivots'); 

    } else if (i == 2) {
        $("#discover_pivotlist").html($("#_heavy").html());
        $("#dialog_pivots").dialog("open");
        $("#dialog_pivots").dialog("option", "title", 'Heavy Pivots'); 

    } else if (i == 20) {
        $("#discover_pivotlist").html($("#_topdomains").html());
        $("#dialog_pivots").dialog("open");
        $("#dialog_pivots").dialog("option", "title", 'Top Domains'); 

    } else if (i == 30) {
        $("#discover_pivotlist").html($("#_recent_projects").html());
        $("#dialog_pivots").dialog("open");
        $("#dialog_pivots").dialog("option", "title", 'Active Projects'); 
    }
}








function feedback() {
    $("#feedback-dialog-content").show();
    $("#feedback-dialog-content-wait").hide();
    $("#feedback-dialog-content-postsubmit").hide();
	$("#dialog_feedback").dialog("open");
}

function feedback_submit() {
    $("#feedback-dialog-content").hide();
    $("#feedback-dialog-content-wait").show();
    $("#feedback-dialog-content-postsubmit").hide();        

    msg = { 
        "msg": $("#feedback_text").val(),
        "email": $("#feedback_email").val()
    }
    $.ajax({
        type: 'POST',
        url: "/about",
        data: msg,
        success: function(){
            $("#feedback-dialog-content-wait").hide();
            $("#feedback-dialog-content-postsubmit").show();        
        }
    });
    
    return false;
}



var is_more_shown = false;
function toggle_more() {
    if (is_more_shown)
        $("#more").hide();
    else
        $("#more").show();
    is_more_shown = !is_more_shown;
}


var is_orig_shown = false;
var is_orig_loaded = false;
function pivot_toggleorig() {    
    if (is_orig_shown) {
        $("#iframe_orig").hide();
        $("#iframe").show();
        
        $("#txt_showorig").html("Show original website");
        $("#pivoticon").removeClass("disabled");        
    } else {
        if (!is_orig_loaded) {
            document.getElementById("iframe_orig").src = url;
            is_orig_loaded = true;
        }        
        $("#iframe_orig").show();
        $("#iframe").hide();
        $("#txt_showorig").html("Show custom variation");
        $("#pivoticon").addClass("disabled");        
    }
    is_orig_shown = !is_orig_shown;
    //is_more_shown = true;
    //toggle_more();
}

function toggle_star() {
    $.ajax({
        type: 'POST',
        url: "/ajax/star",
        data: {'action': (is_starred) ? "-1" : "1"},
        success: function(){
        }
    });
    if (is_starred) {
        $("#staricon").removeClass("enabled");
        $("#staricon").addClass("disabled");
    } else {
        $("#staricon").removeClass("disabled");
        $("#staricon").addClass("enabled");
    }
    is_starred = !is_starred;
}

function signin(continue_to) {
    $("#continue").val(continue_to);
    $("#dialog_signin").dialog("open");
}