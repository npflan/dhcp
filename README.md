# NPF DHCPd on Kubernetes

This repo represents our efforts to run isc-dhcpd on kubernetes, in an active-active configuration, with kubernetes replication controllers and persistent storage for lease databases.

### Quickstart

First upload the config to kubernetes [configmap](https://kubernetes.io/docs/tasks/configure-pod-container/configmap/)

``` shell
kubectl create namespace dhcp
kubectl apply -f k8s-dhcp-config.yaml
python3 config/isc_dhcp_config_gen.py > dhcpd.conf
kubectl create configmap dhcpd --from-file=dhcpd.conf -n dhcp
```

Then you can create the deployments and services with

``` shell
kubectl apply -f k8s-dhcp.yml
```

This essentially concludes the deployment of a redundant active-active DHCPd cluster.

### Strategy for kubernetes operations

This deployment uses several kubernetes features, these are mostly driven by assumptions and limitations of the old isc-dhcpd. The key points are:

-  Isc-dhcpd must know the address of itself and its failover peers at config time, this obviously conflicts with kubernetes pod addressing and self-healing features, isc-dhcpd does however allow DNS resolution of these values, so we use kubernetes [dns records for pods and services](https://kubernetes.io/docs/concepts/services-networking/dns-pod-service/) to overcome these
-  Isc-dhcpd stores its dhcp leases in a file, but it does not create the file automatically on startup. To ensure this always works as intended we use an [init container](https://kubernetes.io/docs/concepts/workloads/pods/init-containers/), to touch the file before starting dhcpd itself
-  While a pod can DNS query its own FQDN to find its own IP, it cannot query other pods IPs by their FQDN, this derailed the process for a while, but it's actually neatly solved by making a [headless service](https://kubernetes.io/docs/concepts/services-networking/service/#headless-services), which will expose its pods IP addresses via DNS.
-  The deployment and services are actually split into two; primary and secondary. This is a bit of a workaround, because dhcpd requires the configs for each instance to be slightly different, so we accomplish this by having two of everything, the advantage of still doing a deployment is that we get a replication controller to spin up a replacement instance if one fails.
-  The two deployments share most of their config, except from a few details, so we can have a kubernetes [configmap](https://kubernetes.io/docs/tasks/configure-pod-container/configmap/) with the shared config, and then the few different details which kubernetes will mount inside the pod, on the same location for the primary and secondary.
-  Since we have two deployments, we want to make sure they don't get deployed on the same physical node in the cluster, for this we use [anti-affinity](https://kubernetes.io/docs/concepts/configuration/assign-pod-node/#affinity-and-anti-affinity) so kubernetes will prefer to place it on separate nodes.
-  It would possibly be more clean to use the new [statefulset](https://kubernetes.io/docs/concepts/workloads/controllers/statefulset/), so we could avoid the duplicate deployments, this is something to look into for NPF 2018. We do not have support for PersistentVolumeClaims, but only PersistentVolumes in our iSCSI SAN, which is maybe a bit hard to do with statefulsets atm.


#### Updating config

Generate new data and upload it to kubernetes. The python script will download the prefixes from netbox directly.

``` shell
python3 config/isc_dhcp_config_gen.py > dhcpd.conf
kubectl create --dry-run configmap dhcpd --from-file=dhcpd.conf -n dhcp -o yaml | kubectl replace -f - -n dhcp
```

After the config is updated, log into a pod in the deployment and test the config. Make sure the new config has been propagated, as there is a TTL cache on kubernetes config maps.

``` shell
dhcpd -t -cf /dhcp/config/dhcpd.conf
```

If the config is syntactically valid, "reload" dhcpd by restarting it, if you just kill dhcpd kubernetes will restart the pod.

``` shell
killall dhcpd
```

### Caveats

- DHCPd is very bad at updating the DNS results for it failover peers, so after the pods have changed IPs, you might need to restart DHCPd so it can pick up the changes.

### TODO

- Readiness / liveness checks
  - Preferably a check that will actually obtain an IP address
- The config values need to be discussed and verified
- OMAPI key should be put in a kubernetes secret
- Metrics for prometheus