var do_everything = function() {
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
        //console.log("window sized", cy_w, cy_h);
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
        exec_resize();

        var elements = [];
        var possibleRoots = new Map();

        dep_graph.nodes.forEach(function(e, i) {
            elements.push({data: {id: "n"+ e.id, label: e.label, type: e.type, dataset_id: e.dataset_id} });
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
                    selector: 'node[type="external"]',
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
                    selector: 'node[type="dataset"]',
                    style: {
                        'background-color': '#6FB1FC',
                        'color': "white",
                        'content': 'data(label)',
                        'shape': 'rectangle',
                        'text-valign': 'center',
                        'text-outline-width': 2,
                        'text-outline-color': '#6FB1FC',
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

            //layout: {
            //    name: 'breadthfirst',
            //    spacingFactor: 0.1,
            //    directed: true,
            //    padding: 10
            //}

            layout: {
                name: 'dagre'
            }

        });

        cy.on('tap', 'node', function(){
            console.log("data", this.data());
            var taiga_id = this.data('dataset_id');
            if (taiga_id) {
                var href = "/dataset/show/"+taiga_id

              try { // your browser may block popups
                window.open( href );
              } catch(e){ // fall back on url change
                window.location.href = this.data('href');
              }
            }

            });
        console.log("done");

    })
}

$(do_everything);

//requirejs(["cytoscape"], function (cytoscape) {
//    console.log("dagre");
//
//    cydagre( cytoscape, dagre ); // register extension
//
//    do_everything();
//})
