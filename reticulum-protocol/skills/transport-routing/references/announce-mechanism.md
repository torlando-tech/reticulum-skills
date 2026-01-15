# Announce Mechanism - Transport Layer Perspective

Extracted from `https://github.com/markqvist/Reticulum/docs/source/understanding.rst` lines 367-430.

---

## The Announce Mechanism in Detail

When an *announce* for a destination is transmitted by a Reticulum instance, it will be forwarded by any transport node receiving it, but according to some specific rules:

* If this exact announce has already been received before, ignore it.

* If not, record into a table which Transport Node the announce was received from, and how many times in total it has been retransmitted to get here.

* If the announce has been retransmitted *m+1* times, it will not be forwarded any more. By default, *m* is set to 128.

* After a randomised delay, the announce will be retransmitted on all interfaces that have bandwidth available for processing announces. By default, the maximum bandwidth allocation for processing announces is set at 2%, but can be configured on a per-interface basis.

* If any given interface does not have enough bandwidth available for retransmitting the announce, the announce will be assigned a priority inversely proportional to its hop count, and be inserted into a queue managed by the interface.

* When the interface has bandwidth available for processing an announce, it will prioritise announces for destinations that are closest in terms of hops, thus prioritising reachability and connectivity of local nodes, even on slow networks that connect to wider and faster networks.

* After the announce has been re-transmitted, and if no other nodes are heard retransmitting the announce with a greater hop count than when it left this node, transmitting it will be retried *r* times. By default, *r* is set to 1.

* If a newer announce from the same destination arrives, while an identical one is already waiting to be transmitted, the newest announce is discarded. If the newest announce contains different application specific data, it will replace the old announce.

Once an announce has reached a transport node in the network, any other node in direct contact with that transport node will be able to reach the destination the announce originated from, simply by sending a packet addressed to that destination. Any transport node with knowledge of the announce will be able to direct the packet towards the destination by looking up the most efficient next node to the destination.

According to these rules, an announce will propagate throughout the network in a predictable way, and make the announced destination reachable in a short amount of time. Fast networks that have the capacity to process many announces can reach full convergence very quickly, even when constantly adding new destinations. Slower segments of such networks might take a bit longer to gain full knowledge about the wide and fast networks they are connected to, but can still do so over time, while prioritising full and quickly converging end-to-end connectivity for their local, slower segments.

## Important Note

Even very slow networks, that simply don't have the capacity to ever reach *full* convergence will generally still be able to reach **any other destination on any connected segments**, since interconnecting transport nodes will prioritize announces into the slower segments that are actually requested by nodes on these.

This means that slow, low-capacity or low-resource segments **don't** need to have full network knowledge, since paths can always be recursively resolved from other segments that do have knowledge about them.

In general, even extremely complex networks, that utilize the maximum 128 hops will converge to full end-to-end connectivity in about one minute, given there is enough bandwidth available to process the required amount of announces.

---

## Path Table Updates

When a transport node receives an announce:

1. Check announce hasn't been seen before (check random_hash)
2. Extract hop count from packet header
3. If hops ≤ PATHFINDER_M (128):
   - Record in announce_table for retransmission
   - Update path_table with:
     - destination_hash → (timestamp, received_from, hops, expires, random_blobs, interface, announce_packet)
4. Queue for rebroadcast with priority = 1/hops (lower hops = higher priority)
5. Retransmit on interfaces with available bandwidth after random delay
6. Listen for retransmission by other nodes
7. If not heard retransmitted, retry up to PATHFINDER_R (1) times with PATHFINDER_G (5 second) grace period

This mechanism ensures:
- Local destinations are quickly reachable
- Distant destinations propagate over time
- Bandwidth is preserved on slow links
- No centralized coordination required
- Network is self-healing and self-organizing
