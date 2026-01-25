function myFullscreenToggle() {
    var canvas = document.getElementById("canvas");
    if (document.fullscreenElement) {
        document.exitFullscreen();
    } else if (canvas) {
        // Try canvas first
        if (canvas.requestFullscreen) {
            canvas.requestFullscreen();
        } else if (canvas.webkitRequestFullscreen) {
            canvas.webkitRequestFullscreen();
        } else if (canvas.msRequestFullscreen) {
            canvas.msRequestFullscreen();
        } else {
            document.documentElement.requestFullscreen();
        }
    } else {
        document.documentElement.requestFullscreen();
    }
}
