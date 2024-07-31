# Alternative rationale for `Yuho`

> [!NOTE]  
> Reasoning here is nearly a carbon  
> copy of Catala's rationale.
>  
> This is now outdated and stored here  
> for archival purposes.

In a bid to automate out inefficiency, many public systems incorporate [programs](https://youtu.be/jmHwAh_-IOU?si=f4DlP7pklN424kCw) *(written in languages like C, COBOL, Java, etc.)* that compute payments to be collected and disbursed, especially in the areas of income, housing and corporate tax. 

However, these computations are often written by programmers who have little understanding of the actual legislation invoked to arrive at the given valuation. As such, the only way to ensure the correctness of these programs is through unit tests which must be calculated and handwritten by lawyers. Due to the aforementioned intricacies and many exceptions found in the law, the number of unit tests quickly skyrockets into the thousands. Moreover, inevitable modifications to existing legislation effectively mean these unit tests have to be rewritten multiple times, wasting many manhours. 

Ultimately, the tedium of such a task means most programs in this vein fail the minimum requirements of [sufficient unit testing](https://daedtech.com/unit-testing-enough/), resulting in large-scale undertesting that causes [costly failures](https://inria.hal.science/hal-02936606v1/document).
