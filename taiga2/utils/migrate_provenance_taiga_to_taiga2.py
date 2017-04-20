import argparse
import csv
import logging
import sys

from sqlalchemy.orm.exc import NoResultFound

from taiga2.api_app import create_app
from taiga2.controllers import models_controller

log = logging.getLogger(__name__)


def populate_db(edges_file_path, nodes_file_path, graphs_file_path):
    # Populate graphs
    print("\n")
    print("Adding the graphs:")
    with open(graphs_file_path) as graph_file:
        reader = csv.DictReader(graph_file, dialect="excel-tab")

        for row in reader:
            graph_id = row['graph_id']
            graph_permaname = row['permaname']
            graph_name = row['name']
            graph_user_id = row['created_by_user_id']
            graph_created_timestamp = row['created_timestamp']

            if not models_controller.get_provenance_graph(graph_permaname):
                print("\tAdding graph {} with permaname {}".format(graph_name, graph_permaname))
                models_controller.add_graph(graph_id=graph_id,
                                            graph_permaname=graph_permaname,
                                            graph_name=graph_name,
                                            graph_user_id=graph_user_id,
                                            graph_created_timestamp=graph_created_timestamp)
            else:
                log.warning("\tThe graph {} already exists in the database".format(graph_permaname))

    # Populate nodes
    print("\n")
    print("Adding the nodes:")
    with open(nodes_file_path) as node_file:
        reader = csv.DictReader(node_file, dialect="excel-tab")

        for row in reader:
            node_id = row['node_id']
            graph_id = row['graph_id']
            dataset_version_id = row['dataset_id']
            label = row['label']
            type = row['type']

            if not models_controller.get_provenance_node(node_id):
                print("\tAdding node {}".format(node_id))
                try:
                    models_controller.add_node(node_id=node_id,
                                               graph_id=graph_id,
                                               dataset_version_id=dataset_version_id,
                                               label=label,
                                               type=type)
                except NoResultFound:
                    log.error("\tThe node {} refers to the datafile id {} which does not exist"
                              .format(node_id, dataset_version_id))

            else:
                log.warning("\tThe node {} already exists in the database".format(node_id))

    # Populate edges
    print("\n")
    print("Adding the edges:")
    with open(edges_file_path) as edge_file:
        reader = csv.DictReader(edge_file, dialect="excel-tab")

        for row in reader:
            edge_id = row['edge_id']
            from_node_id = row['from_node_id']
            to_node_id = row['to_node_id']
            label = row['label']

            if not models_controller.get_provenance_edge(edge_id):
                print("\tAdding edge {}".format(edge_id))
                try:
                    models_controller.add_edge(edge_id=edge_id,
                                               from_node_id=from_node_id,
                                               to_node_id=to_node_id,
                                               label=label)
                except NoResultFound:
                    log.error("\tThe edge {} refers to the nodes {} and {}. One of them does not exist"
                              .format(edge_id, from_node_id, to_node_id))
            else:
                log.warning("\tThe edge {} already exists in the database".format(edge_id))

    print("\n")
    print("Provenance migration done!")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument("-s", "--settings", required=True,
                        help="Settings used for the creation of the api/backends apps")

    parser.add_argument("-e", "--edges", required=True,
                        help="TSV file path of the edges")

    parser.add_argument("-n", "--nodes", required=True,
                        help="TSV file path of the nodes")

    parser.add_argument("-g", "--graphs", required=True,
                        help="TSV file path of the graphs")

    args = parser.parse_args()

    settings_file_path = args.settings
    edges_file_path = args.edges
    nodes_file_path = args.nodes
    graphs_file_path = args.graphs

    api_app, backend_app = create_app(settings_file=settings_file_path)

    with backend_app.app_context():
        populate_db(edges_file_path=edges_file_path,
                    nodes_file_path=nodes_file_path,
                    graphs_file_path=graphs_file_path)
