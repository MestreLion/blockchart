template = """
<html>
    <head>
        <title>MC Ore Distribution Chart</title>
        <script language="javascript" type="text/javascript" src="http://raw.github.com/flot/flot/master/jquery.js"></script>
        <script language="javascript" type="text/javascript" src="http://raw.github.com/flot/flot/master/jquery.flot.js"></script>
    </head>
    <body>
    <h1>Block Distribution per Chunk by Height</h1>

    <div id="placeholder" style="width:66%;height:800px;float:left;"></div>

    <div id="choices" style="width:33%; columns:2; -moz-columns:2; float:right;">Show:</div>
    <br>
    <div id="footer">Yet another minecraft analyzer.<br>&copy;2012 TR. Uses NBT and flot.</div>
    <script type="text/javascript">
    $(function () {
        var datasets = {};

        // hard-code color indices to prevent them from shifting as
        // countries are turned on/off
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
                    series: { lines: { steps: true}},
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
                    }, xaxis: {
                        ticks: function tick50(axis) {
                            var res = [], i = 0;
                            do {
                                res.push(i);
                                i++;
                                if (axis.max >  35) i++;
                                if (axis.max >  70) i++;
                                if (axis.max > 120) i+=2;
                            } while (i <= axis.max);

                            return res;
                        }
                    }
                });
        }

        plotAccordingToChoices();

    });
    </script>

    </body>
</html>
"""