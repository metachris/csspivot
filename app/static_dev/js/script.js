/* Author: 

*/


var previewWindow;    
function preview(showdialog) {
    var form = document.createElement("form");
    form.setAttribute("method", "post");
    form.setAttribute("action", "/preview");
    
    // setting form target to a window named 'formresult'
    //form.setAttribute("target", "previewWindow");
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





















