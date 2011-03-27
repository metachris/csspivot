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
                if (cnt) { if (cnt > 0) cnt_txt = " &middot; " + cnt + " style"; if (cnt > 1) cnt_txt += "s"; }
                url = localStorage.getItem("pivots_recentlyviewed" + k + "_" + arr[i] + "_url");
                out += "<li><a href='/" + arr[i] + "' title='" + url + "'>" + arr[i] + "</a> &middot; <small>" + url + cnt_txt + "</small></li>";
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
    }
}













