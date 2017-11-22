function prepareFrame() {
    ifrm = document.createElement("iframe");
    ifrm.setAttribute("src", "http://{{domain}}/feedback?t={{ token }}");
    ifrm.style.width = "400px";
    ifrm.style.height = "510px";
    ifrm.style.position = "fixed";
    ifrm.style.bottom = 0;
    ifrm.style.right = 0;
    ifrm.style.border = 'none';
    ifrm.style.overflow = 'hidden';
    //ifrm.style.display = 'none';
    document.body.appendChild(ifrm);
}
prepareFrame();


window.addEventListener("message", function (event) {
    if (event.data == "close") {
        document.body.removeChild(ifrm);
    }
}, false);
