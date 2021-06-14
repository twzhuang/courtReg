(function () {

    var clockElement = document.getElementById( "clock" );

    function updateClock ( clock ) {
        clock.innerHTML = new Date().toLocaleTimeString();
    }

    setInterval(function () {
        updateClock( clockElement );
    }, 1000);

    var start_time_arr = document.getElementsByClassName( "start_time" );
    var court_timer = document.getElementsByClassName( "timer" );

    function getEndTime ( start_time_arr ) {
        for (var i = 0; i < start_time_arr.length; i++) {
            court_start_time = start_time_arr[i].textContent;

//          Create Date object for start_time so we can calculate the time remaining
            if (court_start_time != "") {
                let d = new Date();
                let [hours, minutes, seconds] = court_start_time.split(":")

                d.setHours(+hours);
                d.setMinutes(minutes);
                d.setSeconds(seconds);

//              Create a new Date object for end_time and add appropriate minutes
                end_time = new Date(d.getTime());
                end_time.setMinutes(end_time.getMinutes() + 30);

                var x = setInterval(function(end_time, i) {
                    console.log("i: " + i);
                    var now = new Date().getTime();

                    var diff = end_time.getTime() - now;

                    // Time calculations for days, hours, minutes and seconds
//                    var days = Math.floor(distance / (1000 * 60 * 60 * 24));
//                    var hours = Math.floor((distance % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
                    var minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
                    var seconds = Math.floor((diff % (1000 * 60)) / 1000);
                    seconds = seconds.toString().padStart(2, '0');

                    document.getElementById("time_remaining_" + (i+1)).innerHTML = minutes + ":" + seconds

                    if (diff < 0) {
                        clearInterval(x);
//                      Include code here to let server.py know that we can move the next on players to the current
//                      Will probably need AJAX
                    }
                }, 1000, end_time, i)
            }
        }
    }
    getEndTime(start_time_arr)
}());
