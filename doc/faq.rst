Frequently asked questions (FAQ)
================================

An error has been raised. What should I do?
-------------------------------------------

The first thing to do is to read the error message which might contain information on how to resolve it. If not, check the FAQ
section (yes, this one) to see if the error has been explained in more depth. If the error persists or if you do not
understand the error, please post it in the "issues" section on `GitHub
<https://github.com/NMRTeamTBI/MultiNMRFit/issues>`_. We will try to respond as quickly as possible to solve your problem.

Which model should I use?
------------------------------------------------------------------

The choice of the model depends on the signal you want to process. We provide a
set of models in multiNMRFit. If you have a specific signal that is not 
included in the models, you can create your own model. We would be happy to 
include it in the distribution of multiNMRFit. Please post it in the "issues" section on `GitHub
<https://github.com/NMRTeamTBI/MultiNMRFit/issues>`_.

How can I check if my data has been fitted correctly?
------------------------------------------------------------------

The quality of the fit can be evaluated based on the plots of experimental vs 
simulated data for the best fit, which should be as close as possible.

My spectrum hasn't been correctly fitted. Why?
------------------------------------------------------------------

A possible reason to explain a bad fit is that you did not select the 
right model(s). For instance, if you use a
quartet model (i.e. with intensities 1:3:3:1) to fit a doublet of 
doublet (i.e. with intensities 1:1:1:1), the spectrum will not be fitted correctly.

In some situations, it may also be because some parameters have to be
tweaked to help multiNMRFit fit the spectrum, which results in
obviously aberrant fits (e.g. with flat spectrum). If
this situation happens, we suggest modifying the initial values of some parameters to obtain 
a simulated spectrum as close as possible to the experimental one, and re-run the fitting. For
more info on the parameters and how they may affect the fitting process,
please refer to section :ref:`parameters`.

If you think the problem is in multiNMRFit, we would greatly appreciate 
if you could open a new issue on our `issue tracker <https://github
.com/NMRTeamTBI/MultiNMRFit/issues>`_.
   
I cannot start PhysioFit graphical user interface, can you help me?
-------------------------------------------------------------------

If you  installed multiNMRFit following our standard procedure and that you are unable
to start multiNMRFit by opening a terminal and typing :samp:`nmrfit`, then there is indeed
something wrong. Do not panic, we are here to help!
Please follow this simple procedure:

1. The first step of the debugging process will be to get a *traceback*, i.e.
   a message telling us what is actually going wrong. You should see this message in the terminal you opened.

2. Read the traceback and try to understand what is going wrong:

   * If it is related to your system or your Python installation, you will need to ask some
     help from your local system administrator or your IT department so they could
     guide you toward a clean installation. Tell them that you wanted "to use the graphical
     user interface of multiNMRFit, a Python 3.8+ software" and what you did so
     far (installation), give them the traceback and a link toward the
     documentation. They should know what to do.
   * If you believe the problem is in multiNMRFit or that your local system administrator
     told you so, then you probably have found a bug! We would greatly appreciate
     if you could open a new issue on our `issue tracker  <https://github.com/NMRTeamTBI/MultiNMRFit/issues>`_.

I have develop a new signal model, can you include it in multiNMRFit distribution?
--------------------------------------------------------------------------

If you have developed a new signal model, we would be happy to include it in PhysimultiNMRFitoFit! 
Open a new issue on our `issue tracker  <https://github.com/NMRTeamTBI/MultiNMRFit/issues>`_, 
and let's discuss about your model and how we could include it! :)

Examples of how to use PhysioFit programmatically can be found in the section :ref:`testing_the_model`, which offers demonstrations on running simulations and flux calculations.

I would like a new feature.
------------------------------------------------------------------

We would be glad to improve PhysioFit. Please get in touch with us `here 
<https://github.com/MetaSys-LISBP/PhysioFit/issues>`_ so we could discuss your problem.
