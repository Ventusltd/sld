# Manufacturer drawing and product libraries

Reviewed 25 September 2026 using official manufacturer sources. These are useful
product-specific engineering references. Download availability is recorded separately
from permission to redistribute a library publicly. No manufacturer drawings or
macros were copied into this repository during this review.

| Manufacturer | Verified official library and contents | Access and import status |
| --- | --- | --- |
| Eaton | [eCAD, mCAD and EPLAN portals](https://www.eaton.com/ca/en-gb/support/tools/ecad-mcad-eplan-.html): electrical macros, native and DXF/DWG formats, 2D/3D mechanical geometries, EPLAN Electric P8 and Pro Panel data. Eaton lists more than 30,000 products in EPLAN. [Self-service download centre](https://ecat.eaton.com/download-center?locale=de) exposes product master data, ETIM/eClass classification, DWG/STEP/EDZ, drawings and datasheets. | Eaton identifies personal accounts for eCAD and PARTcommunity access. Suitable for checking exact product geometry and attributes. Public redistribution permission must be established for each selected export. |
| ABB | [LV engineering databases](https://new.abb.com/low-voltage/cs/podpora/software-a-aplikace) identify EPLAN, ElProCAD, VEROX, PCSCHEMATIC, ELCAD, EngineeringBase and CAD drawing data. [ABB PLC resources](https://www.abb.com/global/en/areas/motion/plc/programmable-logic-controllers) link CAD drawings, device descriptions and EPLAN product data. [System pro E energy](https://new.abb.com/low-voltage/products/enclosures/Sub-distribution-boards/system-pro-e-energy) provides STEP drawings and directs configurator users to ABB Connect Partner Hub for technical drawings and bills of materials. | Public reference/download pages coexist with a partner configuration route. Access to an engineering database is not an open redistribution licence. Record the particular file's terms before importing it. |
| Schneider Electric | [CAD and BIM resources](https://www.se.com/us/en/work/support/resources-and-tools/cad-drawings/) offer over 2,000 2D CAD drawings, LayoutFAST and a BIM library including switchboards, transformers, metering and panelboards. [Official EPLAN FAQ](https://www.se.com/es/es/faqs/FA344229/) points to EPLAN product data, Schneider Germany's macro downloads and TraceParts dimensions/models; [macro download record](https://www.se.com/bg/bg/download/document/Eplan_Macros_SchneiderElectric/) supplies a concrete catalogue entry. | The BIM library requests login; EPLAN availability depends on the individual product record and portal entitlement. CAD/BIM geometry and EPLAN electrical attributes should be evaluated separately. Public redistribution rights are not established by these download listings. |
| Siemens | [Documentation/downloads hub](https://www.siemens.com/et-ee/support/documentation-downloads/) links CAx Download Manager for 2D/3D models, wiring diagrams and product specifications. A [specific 3UF7510-1AA00-0 product record](https://mall.industry.siemens.com/goos/catalog/Pages/mmpdata.ashx?MLFB1=3UF7510-1AA00-0&lang=en) links product-specific CAx generation and the image database, including circuit diagrams and EPLAN macros. | CAx is a manufacturer engineering-data download route; sign-in or product selection may be requested by the selected service. Siemens' default website terms grant use for the user's own business purposes, not unrestricted public redistribution. |

## Licence findings

This review did not establish an open redistribution licence for the specific OEM
CAD/EPLAN collections above. This is a finding about the reviewed collections,
not a claim that no openly licensed material exists anywhere within these companies.

- [Eaton website terms](https://www.eaton.com/us/en-us/company/policies-and-statements/terms-and-conditions.html)
  default to personal non-commercial downloads unless otherwise specified; software
  has its accompanying licence. Check the CAD portal's specific grant.
- [ABB's current website terms](https://www.abb.com/global/en/company/provider-information)
  restrict reproduction, distribution and modification absent permission and expressly
  say other ABB domains may have different terms. Check each ABB Library document
  and portal's own notice rather than applying the www.abb.com terms indiscriminately.
- [Schneider website terms](https://www.se.com/ww/en/about-us/legal/terms-of-use/)
  reserve rights in text and drawings and restrict reproduction beyond personal,
  non-commercial use without written permission. Product-specific terms may apply.
- [Siemens website terms, section 4](https://www.siemens.com/en-us/terms-of-use/)
  give separately agreed licences precedence; the default licence is non-transferable
  and non-sublicensable and restricts distribution to third parties.

For this public catalogue, retain links and provenance first. An actual asset import
needs a documented licence/permission covering the intended transformation and public
distribution, plus original revision, hash, attribution and part number. Private
engineering use under a vendor agreement is a separate route.

## SLD and IEC interpretation

EPLAN macros can contain electrical symbols, device attributes and connection
information; an outline DWG, STEP enclosure or BIM object may only describe physical
geometry. ETIM/eClass classification is product metadata, not an IEC circuit-symbol
licence. The reviewed portals therefore provide promising product-specific inputs,
but each candidate still needs terminal mapping, units, variant/revision and standards
evidence before becoming an enabled SLD component. A published application schematic
is a reference example, not a project-approved drawing.

## ABB 800 V AC application reference

ABB lists **9AKK108470A5778**, *System pro E Power configurations for 800V AC
combiners in photovoltaic plants. IEC Commercial & Industrial scale*, as an
application note on its [System pro E power product page](https://new.abb.com/low-voltage/fr/produits/enveloppes/system-pro-e-power/system-pro-e-power).
The indexed [English revision C PDF](https://library.e.abb.com/public/5428d9b48eda4971812112c21e134953/9AKK108470A5778_en_C_System%20pro%20E%20Power%20configurations%20for%20800V%20AC%20combiners%20in%20photovoltaic%20plants.%20IEC%20Commercial%20%26%20Industrial%20scale.pdf)
describes string inverters collected into an LV AC combiner, followed by an LV/MV
transformer and MV switchgear. It is useful architecture evidence; it does not confer
approval on a particular site design. Preserve the exact revision when citing its
ratings, because the current index and the [older English revision B](https://library.e.abb.com/public/095df3c747ac40809ea7c0288323ca3e/9AKK108470A5778_en_B_System%20pro%20E%20Power%20configurations%20for%20800V%20AC%20combiners%20in%20photovoltaic%20plants.%20IEC%20Commercial%20%26%20Industrial%20scale.pdf)
are different records. Direct PDF retrieval was unavailable during this review, so
the revision B example's numerical ratings have not been independently confirmed here.
