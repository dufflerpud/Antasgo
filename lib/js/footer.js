//@HDR@	$Id$
//@HDR@		Copyright 2024 by
//@HDR@		Christopher Caldwell/Brightsands
//@HDR@		P.O. Box 401, Bailey Island, ME 04003
//@HDR@		All Rights Reserved
//@HDR@
//@HDR@	This software comprises unpublished confidential information
//@HDR@	of Brightsands and may not be used, copied or made available
//@HDR@	to anyone, except in accordance with the license under which
//@HDR@	it is furnished.
//////////////////////////////////////////////////////////////////////////
//	footer.js	- Routines used by footer of all app pages.	//
//////////////////////////////////////////////////////////////////////////

function footerfunc( fnc )
    {
    with( window.document.footerform )
        {
        func.value = fnc;
        submit();
        }
    }
