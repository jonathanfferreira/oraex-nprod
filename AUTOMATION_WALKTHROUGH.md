# ORAEX Automation Architecture: The "Code" Behind the Lab

You requested a way to demonstrate your **Automated Infrastructure**. This guide maps the "Manual DBA Tasks" to the specific **Code** in your repository. Use this to show your colleague how you converted "ClickOps" into "DevOps".

---

## Phase 1: The Hardware (Infrastructure as Code)
**Manual Equivalent**: Buying servers, cabling networking, buying SAN storage.
**Your Code**: `Vagrantfile`

Open `Vagrantfile` and show:
- **Lines 18-35**: "Here we define the **RAM and CPU** for the Standalone Server."
- **Lines 60-89**: "Here we define the **Shared ASM Disks** (SAN Simulation). Note how we create virtual disks via code."
- **Lines 49**: "Here is the **Private Interconnect** network for RAC."

---

## Phase 2: OS Configuration (Ansible)
**Manual Equivalent**: Installing Linux packages, editing `/etc/sysctl.conf`, creating users `oracle`, `grid`.
**Your Code**: `ansible/roles/oraex_os_bootstrap`

Open `ansible/roles/oraex_os_bootstrap/tasks/main.yml`:
- Explain that this Role handles:
    1.  **Kernel Parameters**: Automatically calculates hugepages and limits.
    2.  **Package Installation**: Installs `oracle-database-preinstall-19c`.
    3.  **Users/Groups**: Creates `oinstall`, `dba` groups with correct IDs.

---

## Phase 3: Grid Infrastructure & Storage (Ansible)
**Manual Equivalent**: Running `oracleasm init`, labeling disks, running `gridSetup.sh`.
**Your Code**: `ansible/roles/oraex_grid_install`

Open `ansible/roles/oraex_grid_install`:
- **Disks**: Show how it loops through the disks defined in your inventory to label them for ASM.
- **Installation**: It runs the installer silently using a "Response File" (template).

---

## Phase 4: Database Engine & Creation (Ansible)
**Manual Equivalent**: Running `runInstaller` and `dbca`.
**Your Code**: `ansible/roles/oraex_db_install` & `oraex_db_config`

- **oraex_db_install**: Unzips the Oracle Gold Image and links the binaries.
- **oraex_db_config**: Runs `dbca` to create the database `ORCL` (or similar) based on variables.

---

## 🚀 How to Demo the Automation
Instead of typing manual commands, your demo flow is:

1.  **"The Plan"**: Show `site.yml`. Explain: *"This is our Orchestrator. It defines the order of operations."*
2.  **"The Inventory"**: Show `ansible/inventory/hosts.ini`. Explain: *"This defines our target servers."*
3.  **" The Execution"**:
    **IMPORTANTE: Onde rodar?**
    Você NÃO roda isso *dentro* da VM.
    Você roda no seu **Notebook** (via WSL/Ubuntu), e o Ansible conecta na VM via SSH para fazer o trabalho.
    
    Run this command (from WSL):
    ```bash
    cd /mnt/d/antigravity/oraex-nprod
    # Fix for WSL "World Writable" warning:
    export ANSIBLE_CONFIG=./ansible.cfg
    
    ansible-playbook site.yml
    ```
    *Explain:* "Now Ansible is connecting to the VM we created and applying all those roles sequentially."

4.  **Verification**:
    SSH into the VM.
    *   **WSL Users**: Use `vagrant.exe ssh` (calls Windows binary).
    *   **PowerShell Users**: Use `vagrant ssh`.
    
    Once inside, run the following checks:

    *   **Check Processes**:
        ```bash
        ps -ef | grep pmon
        ```
        (You should see `asm_pmon_+ASM` and `ora_pmon_ORCL`)

    *   **Check Listener**:
        ```bash
        lsnrctl status
        ```
        (Should show service `ORCL` and `ORCLPDB` as READY)

    *   **Login to Database**:
        ```bash
        sqlplus system/Oracle123@localhost:1521/ORCL
        ```
        (Should connect successfully)

    *   **Check ASM Disks**:
        ```bash
        sudo /u01/app/19.0.0/grid/bin/crsctl stat res -t
        ```
        (Should show `ora.dsk.data` as ONLINE)

5.  **Monitoring Logs (Real-time)**:
    If you want to show the installation running in real-time during the demo:
    ```bash
    # On the VM:
    tail -f /u01/app/oraInventory/logs/GridSetupActions*/installActions*.log
    ```

6.  **Next Session (Restarting Clean)**:
    If you needed to resize disks (FRA 20GB) or restart the lab:
    ```bash
    vagrant destroy -f
    vagrant up
    export ANSIBLE_CONFIG=./ansible.cfg && ansible-playbook site.yml --ask-vault-pass
    ```
