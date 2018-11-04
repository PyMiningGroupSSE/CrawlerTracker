$(document).ready(function () {
    setInterval(function (){
        fetch_nodes();
        fetch_count();
    }, 1000);
});

function fetch_nodes() {
    jQuery.ajax('/api/v1/nodes', {
        type: 'GET',
        success: function (response) {
            if(response.status === 'success') {
                renew_table(response.data);
            }
        }
    });
}

function fetch_count() {
    jQuery.ajax('/api/v1/newscount', {
        type: 'GET',
        success: function (response) {
            if(response.status === 'success') {
                var count = document.getElementById("totalCount");
                count.innerText = response.data["totalCount"];
            }
        }
    });
}

function add_node(nodesTable, node_data) {
    newRow = nodesTable.insertRow();
    newRow.id = node_data.id;
    newRow.insertCell().innerText = node_data.id;
    newRow.insertCell().innerText = node_data.ip;
    newRow.insertCell().innerHTML = "<span class=\"badge badge-success\">Running</span>";
    newRow.insertCell().innerText = node_data.count;
}

function disable_node(nodesTable, row_index) {
    nodeRow = nodesTable.rows[row_index];
    nodeRow.id = "";
    nodeRow.cells[2].innerHTML = "<span class=\"badge badge-danger\">stopped</span>";
}

function renew_table(nodes_dict) {
    var nodesTable = document.getElementById("nodesTable");
    for (var i = 1; i < nodesTable.rows.length; i++) {
        var cur_row = nodesTable.rows[i];
        if(cur_row.id in nodes_dict) {
            var nodeinfo = nodes_dict[cur_row.id];
            cur_row.cells[1].innerText = nodeinfo.ip;
            cur_row.cells[3].innerText = nodeinfo.count;
            delete nodes_dict[cur_row.id];
        } else {
            disable_node(nodesTable, i);
        }
    }
    for (var id in nodes_dict) {
        add_node(nodesTable, nodes_dict[id]);
    }
}