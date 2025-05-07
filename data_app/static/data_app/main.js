document.addEventListener("DOMContentLoaded", function () {
    console.log("main.js załadowany");

    const mainChartDiv = document.getElementById("main-chart");
    const sliceChartXDiv = document.getElementById("slice-chart-x");
    const sliceChartYDiv = document.getElementById("slice-chart-y");
    const parameterChartDiv = document.getElementById("parameter-chart");
    const parameterSelect = document.getElementById("parameter");
    const parameterBtn = document.querySelector("button[onclick*='loadParameterPlot']");
    const timeUnitSelect = document.getElementById("time-scale");

    function getSelectedScale() {
        return timeUnitSelect?.value || "seconds";
    }

    function applyCrosshair(gd) {
        Plotly.relayout(gd, {
            'xaxis.showspikes': true,
            'yaxis.showspikes': true,
            'xaxis.spikemode': 'across',
            'yaxis.spikemode': 'across',
            'xaxis.spikesnap': 'cursor',
            'yaxis.spikesnap': 'cursor',
            'xaxis.spikecolor': 'gray',
            'yaxis.spikecolor': 'gray',
            'xaxis.spikethickness': 1,
            'yaxis.spikethickness': 1,
            'hovermode': 'closest'
        });
    }

    function setupPlotlyClickAndHover(gd) {
        if (gd._boundEvents) return;
        gd._boundEvents = true;

        gd.on('plotly_click', function (data) {
            const point = data.points?.[0];
            if (!point || point.pointIndex === undefined || point.y === undefined) {
                console.warn("Niepoprawne kliknięcie:", point);
                return;
            }

            const xIndex = Array.isArray(point.pointIndex) ? point.pointIndex[1] : point.pointIndex;
            const y = point.y;
            const scale = getSelectedScale();

            fetch(`/get_approximation_x/?x=${xIndex}&scale=${scale}`)
                .then(res => res.json())
                .then(data => {
                    if (data.error) {
                        console.error("Aproksymacja X – błąd:", data.error);
                        return;
                    }
                    Plotly.newPlot(sliceChartXDiv, data.traces, data.layout).then(applyCrosshair);
                })
                .catch(err => console.error("Błąd przy aproksymacji X:", err));

            fetch(`/get_approximation_y/?y=${y}&scale=${scale}`)
                .then(res => res.json())
                .then(data => {
                    if (data.error) {
                        console.error("Aproksymacja Y – błąd:", data.error);
                        return;
                    }
                    Plotly.newPlot(sliceChartYDiv, data.traces, data.layout).then(applyCrosshair);
                })
                .catch(err => console.error("Błąd przy aproksymacji Y:", err));
        });

        gd.on('plotly_hover', () => applyCrosshair(gd));
    }

    function setupMainChart() {
        const chart = mainChartDiv?.querySelector(".js-plotly-plot");
        if (chart && chart._fullLayout) {
            console.log("Podpinam zdarzenia Plotly");
            setupPlotlyClickAndHover(chart);
        } else {
            console.warn("Nie znaleziono instancji Plotly w #main-chart");
        }
    }

    function reloadPageWithNewScale() {
        const newScale = getSelectedScale();
        const url = new URL(window.location.href);
        url.searchParams.set("scale", newScale);
        window.location.href = url.toString();
    }

    function loadParameterPlot() {
        const param = parameterSelect?.value;
        const scale = getSelectedScale();
        if (!param) return;

        fetch(`/get_process_plot/?parameter=${encodeURIComponent(param)}&scale=${scale}`)
            .then(res => res.json())
            .then(data => {
                if (data.error) {
                    console.error("Błąd pobierania wykresu parametru:", data.error);
                    return;
                }
                Plotly.newPlot(parameterChartDiv, data.traces, data.layout);
            })
            .catch(err => console.error('Błąd pobierania wykresu parametru:', err));
    }

    if (parameterBtn && parameterSelect && parameterChartDiv) {
        parameterBtn.addEventListener('click', loadParameterPlot);
    }

    if (timeUnitSelect) {
        timeUnitSelect.addEventListener('change', reloadPageWithNewScale);
    }

    setTimeout(setupMainChart, 300);
});
