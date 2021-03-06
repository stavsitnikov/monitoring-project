#!/usr/bin/env python2.7

# Note: You can't run this in the same folder (network_common/files) as ujson.so.
# Python will try to load the .so and it will fail since it was built for CL

import json
import subprocess
from output_module import ExportData

sudo = "/usr/bin/sudo"
vtysh = "/usr/bin/vtysh"


def run_json_command(command):
    """
    Run a command that returns json data. Takes in a list of command arguments
    :return: JSON string output from command
    """
    json_str = ''
    try:
        json_str = subprocess.check_output(command)
    except OSError as e:
        print("problem executing vtysh %s " % (e))
        exit(3)

    return json_str


def bgp_neighbor_information():

    # Due to CM-12223, we have to pull neighbor data one at a time.
    # TODO: When this is fixed we can replace the show ip bgp sum
    # command with just "show ip bgp neighbor json" and iterate

    neighbor_sum_output = run_json_command(
        [sudo, vtysh, "-c", 'show ip bgp sum json'])

    # if bgp is not configured no output is returned
    if len(neighbor_sum_output) == 0:
        print("No neighbor output. Is BGP configured?")
        exit(3)

    json_neighbor_sum = json.loads(neighbor_sum_output.decode('utf-8'))

    if len(json_neighbor_sum["peers"]) == 0:
        print("No BGP peers found. Are any BGP peers configured?")
        exit(3)

    # BGP is configured and peers exist.

    data = ExportData("bgpstat")
    num_peers=0
    failed_peers=0

    for peer in json_neighbor_sum["peers"].keys():

        #Check if the current state of the peer is establishes to count number of up peers
        if json_neighbor_sum["peers"][peer]["state"] == "Established":
            num_peers += 1
        else:
            failed_peers += 1


        peer_output = run_json_command(
            [sudo, vtysh, "-c", 'show ip bgp neighbor ' + peer + ' json'])

        if len(peer_output) == 0:
            print("No neighbor output for peer" + peer + ".")
            exit(3)

        peer_output_json = json.loads(peer_output.decode('utf-8'))

        if peer not in peer_output_json:
            print("Provided peer " + peer + " not found.")
            exit(3)
        for stat, value in peer_output_json[peer]["messageStats"].items():
            # bgpstat,host=leaf1,peer=swp2 totalSent=6520
            # print("bgpstat,host=" + socket.gethostname() + ",peer=" + peer + " " + stat.encode('ascii') + "=" + str(value))
            data.add_row({"peer":peer},{stat:str(value)})
    # data.add_row({},{"num_peers":len(json_neighbor_sum["peers"])})
    data.add_row({},{"num_peers":num_peers, "failed_peers":failed_peers})

    #data.show_data()
    data.send_data("cli")

if __name__ == "__main__":

    bgp_neighbor_information()

    exit(0)

