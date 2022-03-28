from logging import critical
from django.shortcuts import render
from django.forms import modelformset_factory
from django.http import Http404, HttpResponse

from .pySlope import (
    Slope,
    Material,
    Udl,
    PointLoad,
)

from .models import (
    SlopeModel,
    MaterialModel,
    UdlModel,
    PointLoadModel,
)

from .forms import (
    SlopeForm,
    MaterialForm,
    UdlForm,
    PointLoadForm,
    AnalysisOptionsForm,
)

def index(request):

    #create formsets
    MaterialFormSet = modelformset_factory(MaterialModel, form=MaterialForm, extra=1)
    UdlFormSet = modelformset_factory(UdlModel, UdlForm, extra = 1)
    PointLoadFormSet = modelformset_factory(PointLoadModel, PointLoadForm, extra=1)

    if request.method == 'GET':
        slope_form = SlopeForm(prefix='slope')
        options_form = AnalysisOptionsForm(prefix='options')

        material_formset = MaterialFormSet(queryset=MaterialModel.objects.none(), prefix='material')
        udl_formset = UdlFormSet(queryset=UdlModel.objects.none(), prefix='udl')
        point_load_formset = PointLoadFormSet(queryset=PointLoadModel.objects.none(), prefix='pointload')

        slope = Slope()
        slope.set_materials(Material())
        plot = slope.plot_boundary().update_layout(height=1200,width=2000).to_html()

        return render(request, 'slope/index.html', {
                'slope_form' : slope_form,
                'material_formset' : material_formset,
                'udl_formset' : udl_formset,
                'point_load_formset' : point_load_formset,
                'options_form' : options_form,
                'plot' : plot,
                'forms' : [
                    ('Slope', slope_form, 'form'),
                    ('Materials', material_formset, 'formset'),
                    ('Udls', udl_formset, 'formset'),
                    ('PointLoads', point_load_formset, 'formset'),
                    ('OptionsForm', options_form, 'form'),
                ]
            })
    
    elif request.method == 'POST':
        # initialize form objects with POST information

        slope_form = SlopeForm(request.POST, prefix='slope')

        material_formset = MaterialFormSet(request.POST, prefix='material')
        udl_formset = UdlFormSet(request.POST, prefix='udl')
        point_load_formset = PointLoadFormSet(request.POST, prefix='pointload')
        
        options_form = AnalysisOptionsForm(request.POST, prefix='options')

        form_list = [
            slope_form,
            material_formset,
            udl_formset,
            point_load_formset,
            options_form,
        ]

        # check is valid
        valid = True
        for a in form_list:
            print(a.errors)
            valid *= a.is_valid()
        
        # if form is valid
        if valid:

            slope = create_slope(*form_list)

            if options_form.cleaned_data['plot_choice'] == 'plot_critical':
                plot = slope.plot_critical()
            else:
                plot = slope.plot_all_planes(
                    max_fos = options_form.cleaned_data['max_display_FOS']
                )

            plot = plot.update_layout(width=2000, height = 1200).to_html()

            return render(request, 'slope/index.html', {
                    'slope_form' : slope_form,
                    'material_formset' : material_formset,
                    'udl_formset' : udl_formset,
                    'point_load_formset' : point_load_formset,
                    'options_form' : options_form,
                    'plot' : plot,
                    'forms' : [
                        ('Slope', slope_form, 'form'),
                        ('Materials', material_formset, 'formset'),
                        ('Udls', udl_formset, 'formset'),
                        ('PointLoads', point_load_formset, 'formset'),
                        ('OptionsForm', options_form, 'form'),
                    ]
                })
    
    return HttpResponse('erroer')

def create_slope(
    slope_form,
    material_formset,
    udl_formset,
    point_load_formset,
    options_form,
    ):

    # create beam object
    if options_form.cleaned_data['slope_choice'] == 'length':
        slope = Slope(
            height = slope_form.cleaned_data['height'],
            length = slope_form.cleaned_data['length'],
        )
    else:
        slope = Slope(
            height = slope_form.cleaned_data['height'],
            length = None,
            angle = slope_form.cleaned_data['angle'],
        )

    # add materials to slope
    for material_form in material_formset.cleaned_data:
        slope.set_materials(
            Material(
                unit_weight=material_form['unit_weight'],
                friction_angle=material_form['friction_angle'],
                cohesion=material_form['cohesion'],
                depth_to_bottom=material_form['depth_to_bottom'],
                name=material_form['name'],
                color=material_form['color'],
            )
        )

    # add point loads to slope
    for point_load_form in point_load_formset.cleaned_data:
        if point_load_form:
            slope.set_pls(
                PointLoad(
                    magnitude = point_load_form['magnitude'],
                    offset= point_load_form['offset'],
                    color = point_load_form['color'],
                    dynamic_offset = point_load_form['dynamic_offset'],
                )
            )

    # add uniform loads to slope
    for udl_form in udl_formset.cleaned_data:
        if udl_form:
            slope.set_udls(
                Udl(
                    magnitude = udl_form['magnitude'],
                    offset = udl_form['offset'],
                    length = udl_form['length'],
                    color = udl_form['color'],
                    dynamic_offset = udl_form['dynamic_offset'],
                )
            )
    
    if options_form.cleaned_data['analysis_choice'] == 'normal':
        slope.analyse_slope()
    else:
        slope.analyse_dynamic(
            critical_fos=options_form.cleaned_data['critical_FOS']
        )
    
    return slope