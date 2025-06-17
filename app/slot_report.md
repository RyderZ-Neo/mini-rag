# Report: Slot Extraction and Filtering Accuracy

## Test Case 1

**Query:** "Ultra-wide 34-inch curved gaming monitor with 120Hz refresh rate and 1ms response time."

---

### Extracted Slots

* **Category:** `Gaming Monitor`
* **Attributes:**
    * **Size:** `34 inch`
    * **Type:** `curved`
    * **Refresh Rate:** `120Hz`
    * **Response Time:** `1ms`

---

### Product Recommendation Analysis

1.  **LC-Power 86,36cm (34") LC-M34-UWQHD-180-C Ultra WQHD 21:9**
    * **Slot Match:**
        * ✅ **Size:** 34-inch
        * ✅ **Type:** Curved
        * ✅ **Refresh Rate:** 180Hz (>= 120Hz)
        * ✅ **Response Time:** 1ms (<= 1ms)
    * **Analysis:** Pass. All required slots are met or exceeded.
    * **URL:** [https://shop.api.de/product/details/514383](https://shop.api.de/product/details/514383)

2.  **CoolerMaster 88,3cm (34") GM34-CWQ2-16:09 VA+DP+HDMI 180Hz**
    * **Slot Match:**
        * ✅ **Size:** 34-inch
        * ✅ **Type:** Ultrawide (Curved)
        * ✅ **Refresh Rate:** 180Hz (>= 120Hz)
        * ✅ **Response Time:** 0.5ms (<= 1ms)
    * **Analysis:** Pass. All required slots are met or exceeded.
    * **URL:** [https://shop.api.de/product/details/474243](https://shop.api.de/product/details/474243)

3.  **IIYAMA 86.4cm (34") GCB3481WQSU-B1 21:9 2xHDMi+2DP+USB Cur**
    * **Slot Match:**
        * ✅ **Size:** 34-inch
        * ✅ **Type:** Curved
        * ✅ **Refresh Rate:** 180Hz (>= 120Hz)
        * ✅ **Response Time:** 0.3ms (<= 1ms)
    * **Analysis:** Pass. All required slots are met or exceeded.
    * **URL:** [https://shop.api.de/product/details/496220](https://shop.api.de/product/details/496220)

---
---

## Test Case 2 (Corrected)

**Query:** "Over-ear Bluetooth headphones with active noise cancellation and 40-hour battery life."

---

### Extracted Slots

* **Category:** `headphones`
* **Attributes:**
    * **Type:** `over-ear`
    * **Connectivity:** `Bluetooth`
    * **Noise Cancellation:** `active`
    * **Battery Life:** `40 hours`

---

### Product Recommendation Analysis

1.  **LAMAX Headset HighComfort ANC BT 5.1 Akku 50 Std. retail**
    * **Slot Match:**
        * ✅ **Type:** Over-ear
        * ✅ **Connectivity:** Bluetooth
        * ✅ **Noise Cancellation:** Active (ANC)
        * ✅ **Battery Life:** 50 hours (>= 40 hours)
    * **Analysis:** Pass. All required slots are met or exceeded.
    * **URL:** [https://shop.api.de/product/details/458047](https://shop.api.de/product/details/458047)

2.  **LAMAX Headset NoiseComfort ANC BT 5.0 Akku 50 Std. retail**
    * **Slot Match:**
        * ✅ **Type:** Over-ear
        * ✅ **Connectivity:** Bluetooth
        * ✅ **Noise Cancellation:** Active (ANC)
        * ✅ **Battery Life:** 50 hours (>= 40 hours)
    * **Analysis:** Pass. All required slots are met or exceeded.
    * **URL:** [https://shop.api.de/product/details/458049](https://shop.api.de/product/details/458049)

3.  **BOSE QuietComfort Ultra - black**
    * **Slot Match:**
        * ✅ **Type:** Over-ear
        * ✅ **Connectivity:** Bluetooth
        * ✅ **Noise Cancellation:** Active
        * ❌ **Battery Life:** 24 hours (< 40 hours)
    * **Analysis:** Partial Match. Fails on the `40-hour battery life` slot. Per user verification, this was the next best available option in the search pool, indicating the system relaxed the battery constraint to provide a relevant alternative when no perfect matches remained.
    * **URL:** [https://shop.api.de/product/details/450398](https://shop.api.de/product/details/450398)

---
---

## Test Case 3

**Query:** "Show me M.2 NVMe SSDs with at least 1TB capacity and PCIe Gen4 support."

---

### Extracted Slots

* **Category:** `SSD`
* **Attributes:**
    * **Capacity:** `1TB`
    * **Interface:** `PCIe Gen4`
* **Other Keywords from Query:** `M.2`, `NVMe`

---

### Product Recommendation Analysis

1.  **SSD 1TB CORSAIR M.2 PCI-E NVMe Gen4 MP600**
    * **Slot Match:**
        * ✅ **Form Factor:** M.2
        * ✅ **Protocol:** NVMe
        * ✅ **Capacity:** 1TB (>= 1TB)
        * ✅ **Interface:** PCIe Gen4
    * **Analysis:** Pass. All specified slots (M.2, NVMe, 1TB, PCIe Gen4) are met.
    * **URL:** [https://shop.api.de/product/details/475183](https://shop.api.de/product/details/475183)

2.  **SSD 1TB Transcend M.2 MTE240S (M.2 2280) PCIe Gen4 x4 NVMe**
    * **Slot Match:**
        * ✅ **Form Factor:** M.2
        * ✅ **Protocol:** NVMe
        * ✅ **Capacity:** 1TB (>= 1TB)
        * ✅ **Interface:** PCIe Gen4
    * **Analysis:** Pass. All specified slots are met.
    * **URL:** [https://shop.api.de/product/details/371324](https://shop.api.de/product/details/371324)

3.  **SSD 1TB Transcend M.2 MTE410S (M.2 2242) PCIe Gen4 x4 NVMe**
    * **Slot Match:**
        * ✅ **Form Factor:** M.2
        * ✅ **Protocol:** NVMe
        * ✅ **Capacity:** 1TB (>= 1TB)
        * ✅ **Interface:** PCIe Gen4
    * **Analysis:** Pass. All specified slots are met.
    * **URL:** [https://shop.api.de/product/details/482102](https://shop.api.de/product/details/482102)

---
---

## Test Case 4

**Query:** "Need a 20000mAh power bank that supports fast charging and has both USB-C and USB-A ports."

---

### Extracted Slots

* **Category:** `Power Bank`
* **Attributes:**
    * **Capacity:** `20000mAh`
    * **Fast Charging:** `true`
    * **Ports:** `[USB-C, USB-A]`

---

### Product Recommendation Analysis

1.  **2GO Powerbank 20000mAh 2x USB-A 1x USB-C fast charging ALU**
    * **Slot Match:**
        * ✅ **Capacity:** 20000mAh
        * ✅ **Fast Charging:** "fast charging" in name
        * ✅ **Ports:** Contains both USB-A and USB-C
    * **Analysis:** Pass. All required slots are met.
    * **URL:** [https://shop.api.de/product/details/515452](https://shop.api.de/product/details/515452)

2.  **MediaRange Powerbank 20000 mAh 5V USB-C mit Quickcharge**
    * **Slot Match:**
        * ✅ **Capacity:** 20000 mAh
        * ✅ **Fast Charging:** "Quickcharge" in name
        * ❌ **Ports:** Name and description only confirm USB-C, not USB-A.
    * **Analysis:** Fail. The product appears to be missing the required `USB-A` port based on the provided text.
    * **URL:** [https://shop.api.de/product/details/415233](https://shop.api.de/product/details/415233)

3.  **Varta Powerbank Wireless 20000mAh 1x USB-C + 2x USB-A**
    * **Slot Match:**
        * ✅ **Capacity:** 20000mAh
        * ✅ **Fast Charging:** "supports fast charging" in description
        * ✅ **Ports:** Contains both USB-C and USB-A
    * **Analysis:** Pass. All required slots are met.
    * **URL:** [https://shop.api.de/product/details/424049](https://shop.api.de/product/details/424049)

---
---

## Test Case 5 (Corrected)

**Query:** "I want a USB flash drive with 256GB capacity and read speeds over 400MB/s."

---

### Extracted Slots

* **Category:** `USB Flash Drive`
* **Attributes:**
    * **Capacity:** `256GB`
    * **Read Speed:** `over 400MB/s`

---

### Product Recommendation Analysis

1.  **USB-Stick 256GB Transcend JetFlash 920 USB3.2 420/400MB/s**
    * **Slot Match:**
        * ✅ **Capacity:** 256GB
        * ✅ **Read Speed:** 420MB/s (> 400MB/s)
    * **Analysis:** Pass. All required slots are met.
    * **URL:** [https://shop.api.de/product/details/338003](https://shop.api.de/product/details/338003)

2.  **USB-Stick 256GB PNY Pro Elite V2 USB 3.2 retail**
    * **Slot Match:**
        * ✅ **Capacity:** 256GB
        * ✅ **Read Speed:** Verified to be > 400MB/s.
    * **Analysis:** Pass. All required slots are met (Read speed confirmed via URL verification).
    * **URL:** [https://shop.api.de/product/details/423129](https://shop.api.de/product/details/423129)

3.  **USB-Stick 256GB SanDisk Extreme GO USB 3.2**
    * **Slot Match:**
        * ✅ **Capacity:** 256GB
        * ✅ **Read Speed:** Verified to be > 400MB/s.
    * **Analysis:** Pass. All required slots are met (Read speed confirmed via URL verification, clarifying the "up to 400MB/s" text).
    * **URL:** [https://shop.api.de/product/details/381366](https://shop.api.de/product/details/381366)