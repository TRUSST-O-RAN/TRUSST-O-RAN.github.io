TRUSST-O-RAN
============

Trustworthy, Resilient, Unified, and Scalable Security Techniques for Open
Radio Access Networks.

The project studies how disaggregated radio access networks maintain state,
coordinate control transitions, and produce trustworthy feedback under
adversarial UE behavior. Its research artifacts separate proposed attack
hypotheses, implemented mechanisms, and measured evidence.

The current organization contains four Thrust 1 tasks. A shared virtual
Open5GS / OCUDU CU-DU / srsUE laboratory provides their initial connectivity
baseline. Task-specific extensions remain necessary for RU-DU fronthaul,
RIC feedback, and selective radio-procedure perturbations.

.. toctree::
   :maxdepth: 2
   :caption: Project

   project
   tasks

.. toctree::
   :maxdepth: 2
   :caption: Laboratory

   virtual-setup
   validation
   evaluation

.. toctree::
   :maxdepth: 2
   :caption: Task 1 implementation

   attack-model
   scenarios
   instrumentation-overview
   instrumentation
   instrumentation-validation
   contributing
