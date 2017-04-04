var I_Hate_Meetings = (function () {

    var counter = document.getElementById("counter");
    var hourCount = document.getElementById("hours");
    var minCount = document.getElementById("mins");
    var secCount = document.getElementById("secs");
    var costCount = document.getElementById("cost");
    var totalSalaries = document.getElementById("totalSalaries");

    var startButton = document.getElementById("start");
    var pauseButton = document.getElementById("pause");
    var stopButton = document.getElementById("stop");
    var salaryInputForm = document.getElementById("salaryInputForm");
    var newSalaryButton = document.getElementById("newSalaryButton");
    var newSalary = document.getElementById("newSalary");

    var salary = 0;
    var numSalaries = 0;

    var start = false,
        stop = false,
        pause = false;

    startButton.onclick = function() {
        start = true;
        stop = pause = false;
    };

    stopButton.onclick = function() {
        stop = true;
        start = false;
        salary = 0;
        numSalaries = 0;
    };

    pauseButton.onclick = function() {
        pause = true;
        start = false;
    };

    newSalaryButton.onclick = function() {
        if (newSalary.value) {
            salary += parseInt(newSalary.value);
            newSalary.value = null;
        }
        numSalaries++;
    };


    setInterval(function() {
        var hours = 0,
            mins = 0,
            secs = 0;
        var cost = 0;
        var count = 0;

        if (start) {
            count = counter.innerHTML;
            count = counter.innerHTML = parseInt(count, 10) + 1;
        }
        else if (stop) {
            count = counter.innerHTML = 0;
        }
        else if (pause) {
            return;
        }

        hours = count / 3600;
        mins = (count / 60) % 60;
        secs = count % 60;
        //7,200,000 = number of work seconds/year
        cost = count * (salary / 7200000);

        hourCount.innerHTML = parseInt(hours, 10);
        minCount.innerHTML = parseInt(mins, 10);
        secCount.innerHTML = parseInt(secs, 10);
        costCount.innerHTML = parseFloat(cost).toFixed(2);
        totalSalaries.innerHTML = "Number of salaries entered: " + parseInt(numSalaries, 10);

    }, 1000);

})();

(function($) {
    "use strict";

    var tipPercent = 15.0;

    var saveSettings = function() {
        try {
            var tipPct = parseFloat( $('#tipPercentage').val() );
            localStorage.setItem('tipPercentage', tipPct);
            tipPercent = tipPct;
            window.history.back();
        } catch (ex) {
            alert('Tip percentage must be a decimal value');
        }
    };

    $( document ).on( "ready", function(){
        $('#saveSettings').on('click', saveSettings);
        var tipPercentSetting = localStorage.getItem('tipPercentage');
        if (tipPercentSetting) {
            tipPercent = parseFloat(tipPercentSetting);
        }
        $('#tipPercentage').val(tipPercent);
    });

}
)(jQuery);

