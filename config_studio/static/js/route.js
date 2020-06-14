const route = [{

        "url": `{{url_for('load_opc_da')}}`,
        "icon": "home",
        "name": "home",
    },
    {

        "url": '/load_opc_ae',
        "icon": "home",
        "name": "opc_da",
    },
    {

        "url": '{{url_for("show_opc")}}',
        "icon": "home",
        "name": "opc_ae",
    },
]



export  {route}