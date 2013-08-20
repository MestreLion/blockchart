template = """
<html>
    <head>
        <title>MC Ore Distribution Chart</title>
        <link href="http://raw.github.com/flot/flot/master/examples/examples.css" rel="stylesheet" type="text/css">
        <script language="javascript" type="text/javascript" src="http://raw.github.com/flot/flot/master/jquery.js"></script>
        <script language="javascript" type="text/javascript" src="http://raw.github.com/flot/flot/master/jquery.flot.js"></script>
        <script language="javascript" type="text/javascript" src="http://raw.github.com/flot/flot/master/jquery.flot.navigate.js"></script>
    </head>
    <body>
    <h1>Block Distribution per Chunk by Height</h1>

    <div id="placeholder" style="width:66%;height:80%;float:left;"></div>

    <div id="choices" style="width:33%; columns:2; -moz-columns:2; float:right;"></div>
    <p/>
    <div id="footer">
        Yet another minecraft analyzer. Uses <a href="http://www.flotcharts.org">flot</a><br>
        Click and drag to pan, double-click or mousewheel to zoom.<br>
        Copyright &copy;2013 MestreLion.
    </div>

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
            choiceContainer.append('<br/><input type="checkbox" name="' + key +
                                   '"' + (val.active ? ' checked="checked"' : '') + ' id="id' + key + '">' +
                                   '<label for="id' + key + '">'
                                    + val.label + '</label>');
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
                        zoomRange: [0.001, 1000],
                        panRange: [-1, 270]
                    },
                    zoom: {
                        interactive: true
                    },
                    pan: {
                        interactive: true
                    }
/*
                    yaxis: {
                        transform: function (v) { return Math.log(v+1); },
                        inverseTransform: function (v) { return Math.exp(v)-1; },
                        ticks:   function logTickGenerator(axis) {
                            var res = [], i = 0.01;
                            do {
                                if (i/2>0.01) { res.push(i/2); res.push(i*2.5) };
                                res.push(i);
                                i*=10;
                            } while (i <= axis.max);

                            return res;
                        }
                    },
*/
                });
        }

        plotAccordingToChoices();

    });
    </script>

    </body>
</html>
"""