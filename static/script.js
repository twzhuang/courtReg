(function () {

    function sendPostReq(courtNum, end_time) {
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
                else if (xhttp.status == 400) {
                   alert('There was an error 400');
                }
                else {
                    alert('something else other than 200 was returned');
                }
            }
        };
        xhttp.send(JSON.stringify({court_number: courtNum, end_time: end_time}))

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
            console.log(`End time UTC from application.py for court number ${i+1}: ${court_end_time}`);



//          End time is currently a string so we need to parse it and create a Date object for it
            if (court_end_time != "") {
//              Parse the court end time and assign to a new variable
//              Datetime object from application.py comes in the following format: 'YYYY-MM-DD HH:MM:SS.mmmmmm'
                var [day, time] = court_end_time.split(" ");
                console.log(`End day: ${day}`);
                console.log(`End time: ${time}`);

                var end_time = new Date(`${day}T${time.split(".")[0]}`);
                console.log(`End time: ${end_time}`);
//                let end_time = new Date();
//                let [hours, minutes, seconds] = court_end_time.split(":")

//                end_time.setHours(+hours);
//                end_time.setMinutes(minutes);
//                end_time.setSeconds(seconds);

                var x = setInterval(function(end_time, i) {
                    var now = new Date()
                    // Convert current time to UTC time
                    now.setDate(now.getUTCDate());
                    now.setMonth(now.getUTCMonth());
                    now.setFullYear(now.getUTCFullYear());
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
                        sendPostReq(i+1, end_time); // Tell server to update courts
                    }
                }, 1000, end_time, i)
            }
        }
    }
    getEndTime(end_time_arr)
}());
