(function () {

    function sendPostReq(courtNum) {
        var xhttp = new XMLHttpRequest();
        xhttp.open("POST", '/updateCourt', true);
        //Send the proper header information along with the request
        xhttp.setRequestHeader("Content-Type", "application/json");


        xhttp.onreadystatechange = function() {
            if (xhttp.readyState == 4) {
                if (xhttp.status == 200) {
                    console.log("POST REQUEST RECEIVED SUCCESSFULLY")
                    window.location.reload();
                }
            }
        };
        xhttp.send(JSON.stringify({court_number: courtNum}))

    }

    var clockElement = document.getElementById( "clock" );

    function updateClock ( clock ) {
        clock.innerHTML = new Date().toLocaleTimeString();
    }

    setInterval(function () {
        updateClock( clockElement );
    }, 1000);

    var end_time_arr = document.getElementsByClassName("end_time");
    var court_timer = document.getElementsByClassName( "timer" );

    function getEndTime ( end_time_arr ) {
        for (var i = 0; i < end_time_arr.length; i++) {
            court_end_time = end_time_arr[i].textContent;

//          End time is currently a string so we need to parse it and create a Date object for it
            if (court_end_time != "") {
                let end_time = new Date();
                let [hours, minutes, seconds] = court_end_time.split(":")

                end_time.setHours(+hours);
                end_time.setMinutes(minutes);
                end_time.setSeconds(seconds);

                var x = setInterval(function(end_time, i) {
                    var now = new Date()
                    // Convert current time to UTC time
                    now.setHours(now.getUTCHours());
                    now.setMinutes(now.getUTCMinutes());
                    now.setSeconds(now.getUTCSeconds());

                    var diff = end_time.getTime() - now.getTime();
                    console.log("end_time: ", end_time)
                    console.log("now: ", now)
                    console.log("diff: ", diff)

                    // Time calculations for minutes and seconds
                    var minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
                    var seconds = Math.floor((diff % (1000 * 60)) / 1000);
                    seconds = seconds.toString().padStart(2, '0');

                    document.getElementById("time_remaining_" + (i+1)).innerHTML = minutes + ":" + seconds

                    if ((diff - 1000) < 0) {
                        console.log("Under 1000")
                        clearInterval(x); // Stop timer
                        sendPostReq(i+1); // Tell server to update courts
                    }
                }, 1000, end_time, i)
            }
        }
    }
    getEndTime(end_time_arr)
}());
