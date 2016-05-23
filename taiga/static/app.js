requirejs(["cytoscape"], function (cytoscape) {

    var resizeTimer;
    var cy = null;

    var exec_resize = function () {
        var container = $(".container");
        var h = $( window ).height();
        var w = container.width();

        var cy_offset = $("#cy").offset();

        var cyel = $("#cy");
        var cy_w = w - 10;
        var cy_h = h - cy_offset.top - 10;
        if (cy_h < 100) {
            cy_h = 100;
        }
        cyel.width(cy_w);
        cyel.height(cy_h);
        console.log("window sized", cy_w, cy_h);
    }

    $(window).on('resize', function (e) {
        clearTimeout(resizeTimer);
        resizeTimer = setTimeout(function () {
            exec_resize();
            if (cy != null) {
                cy.resize();
            }
        }, 250);
    });

    $(function () {
        console.log("hello");

        exec_resize();

        var elements = [];
        var possibleRoots = new Map();

        dep_graph.nodes.forEach(function(e, i) {
            elements.push({data: {id: "n"+ e.id, label: e.label, type: e.type} });
            possibleRoots["n"+ e.id] = true;
        });

        dep_graph.edges.forEach(function(e, i) {
            elements.push({data: {id: "e"+i, source: "n"+e.from_id, target: "n"+ e.to_id } });
            possibleRoots["n"+ e.to_id] = false;
        });

        var rootNodeIds = [];
        possibleRoots.forEach(function(k, v) {
            if(v) {
                rootNodeIds.append(k)
            }
        })

        cy = cytoscape({

            container: document.getElementById('cy'), // container to render in

            elements: elements,

            style: [ // the stylesheet for the graph
                {
                    selector: 'node[type!="process"]',
                    style: {
                        'background-color': '#666',
                        'color': "white",
                        'content': 'data(label)',
                        'shape': 'rectangle',
                        'text-valign': 'center',
                        'text-outline-width': 2,
                        'text-outline-color': '#666',
                        'width': '300',
                    }
                },

                {
                    selector: 'node[type="process"]',
                    style: {
                        'background-color': '#2ff',
                        'label': 'data(label)',
                        'text-valign': 'center',
                        'shape': 'circle'
                    }
                },

                {
                    selector: 'edge',
                    style: {
                        'width': 3,
                        'line-color': '#ccc',
                        'target-arrow-color': '#ccc',
                        'target-arrow-shape': 'triangle'
                    }
                }
            ],

            layout: {
                name: 'breadthfirst',
                spacingFactor: 0.1,
                directed: true,
                padding: 10
            }

        });
        console.log("done");

    })
})