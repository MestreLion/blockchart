template = """
<html>
    <head>
        <title>MC Ore Distribution Chart</title>
        <meta charset="UTF-8" />
        <link href="http://www.flotcharts.org/flot/examples/examples.css" rel="stylesheet" type="text/css">
        <script language="javascript" type="text/javascript" src="http://www.flotcharts.org/flot/jquery.js"></script>
        <script language="javascript" type="text/javascript" src="http://www.flotcharts.org/flot/jquery.flot.js"></script>
        <script language="javascript" type="text/javascript" src="http://www.flotcharts.org/flot/jquery.flot.navigate.js"></script>
        <style type="text/css">
            input[type=checkbox] { margin: 1px 1px 1px 10px; }
            body { font: 15px/1.2em "proxima-nova", Helvetica, Arial, sans-serif; }
        </style>
    <script type="text/javascript">
    $(function () {
        var datasets = {};
        var chunks = 0;

        // hard-code color indices to prevent them from shifting as blocks are turned on/off
        var i = 0;
        $.each(datasets, function(key, val) {
            val.color = i;
            ++i;
        });

        // insert checkboxes
        var choiceContainer = $("#choices");
        $.each(datasets, function(key, val) {
            choiceContainer.append('<input type="checkbox" name="' + key +
                                   '"' + (val.active ? ' checked="checked"' : '') + ' id="id' + key + '">' +
                                   '<label for="id' + key + '">'
                                    + val.label + '</label><br/>');
        });
        choiceContainer.find("input").click(plotAccordingToChoices);


        function showTooltip(pageX, pageY, label, dataX, dataY) {
            $("<div id='tooltip'><b>" + label + "</b> per chunk at height <b>" +
              dataX + "</b> = <b>" + dataY.toFixed(2) + "</b> (total: <b>" + dataY * chunks + "</b>)</div>").css({
                position: "absolute",
                display: "none",
                top: pageY + 5,
                left: pageX + 5,
                border: "1px solid #fdd",
                padding: "2px",
                "background-color": "#fee",
                opacity: 0.80
            }).appendTo("body").fadeIn(200);
        }

        var previousPoint = null;
        $("#placeholder").bind("plothover", function (event, pos, item) {

            if (item) {
                if (previousPoint != item.dataIndex) {
                    previousPoint = item.dataIndex;
                    $("#tooltip").remove();
                    var x = item.datapoint[0],
                    y = item.datapoint[1];
                    showTooltip(item.pageX, item.pageY, item.series.label, x, y);
                }
            } else {
                $("#tooltip").remove();
                previousPoint = null;
            }
        });

        function plotAccordingToChoices() {
            var data = [];

            choiceContainer.find("input:checked").each(function () {
                var key = $(this).attr("name");
                if (key && datasets[key])
                    data.push(datasets[key]);
            });

            if (data.length > 0)
                $.plot($("#placeholder"), data, {
                    grid: { hoverable: true },
                    series: {
                        points: {
                            show: true
                        },
                        lines: {
                            show: true,
                        },
                    },
                    xaxis: {
                        tickDecimals: 0,
                        zoomRange: [0.001, 1000],
                        panRange: [-5, 270]
                    },
                    yaxis: {
/*
                        transform: function (v) { return v==0 ? null : Math.log(v); },
                        inverseTransform: function (v) { return Math.exp(v); },
                        ticks: function logTicks(axis) {
                            var res = [], i = 0.0001;
                            do {
                                res.push(i);
                                res.push(i*2.5);
                                res.push(i*5);
                                i*=10;
                            } while (i <= axis.max);
                            return res;
                        },
*/
                        zoomRange: [0.001, 1000],
                        panRange: [-1, 270]

                    },
                    zoom: {
                        interactive: true
                    },
                    pan: {
                        interactive: true
                    }
                });
        }

        plotAccordingToChoices();

    });
    </script>
    </head>
    <body>

    <div id="header">
        <h2>Block Distribution per Chunk by Height</h2>
    </div>

    <div id="content" style="width: 95%;">
        <div class="demo-container" style="width:100%; height:75%;">
            <div id="placeholder" class="demo-placeholder" style="float:left; width:70%; height:100%;"></div>
            <div id="choices" style="float:right; width:30%; columns:2; -moz-columns:2;"></div>
        </div>
        <p>Click and drag to pan, double-click or mousewheel to zoom.</p>
    </div>

    <div id="footer">
        Yet another minecraft analyzer. Uses <a href="http://www.flotcharts.org">flot</a><br>
        Copyright &copy;2013 MestreLion.
    </div>


    </body>
</html>
"""