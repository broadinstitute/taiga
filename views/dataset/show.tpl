{% extends "base.tpl" %}

{% macro download_link(format) -%}
  <a href="/rest/v0/datasets/{{meta.dataset_id}}?format={{ format }}">{{ format }}</a>
{%- endmacro %}

{% block title %}Dataset{% endblock %}
{% block content %}
  <a href="/">Home</a>
  <h1>Name: {{ meta.name }}</h1>
  <p> Created by {{ meta.created_by }} on {{ meta.created_timestamp }}</p> 
  <p> Version {{ meta.version }}</p>
  <p> Versions: 
    {% for version in versions %} 
      <a href="/dataset/show/{{ version.dataset_id }}">v{{ version.version }}</a>
    {% endfor %}
  </p>
  <p> Download as 
    {{ download_link('hdf5') }} | 
    {{ download_link('tabular_csv') }} | 
    {{ download_link('tabular_tsv') }} | 
    {{ download_link('csv') }} | 
    {{ download_link('tsv') }}</p>
  <p> <a href="/upload/tabular-form?dataset_id={{meta.dataset_id}}">Upload a new version</a> </p>
  <p> Description: </p>
  <p>
    <a href="#" class="x-editable-class" data-name="description" data-type="textarea" data-pk="{{ dataset_id }}" data-url="/dataset/update" data-title="Enter description">{{ meta.description }}</a>
  </p>
  
  <h2>Dimensions</h2>
  
  <table class="table table-bordered table-striped">
    <thead>
      <tr>
          <th></th>
          <th>Description</th>
          <th>Values</th>
      </tr>
    </thead>
    
    <tbody>
      {% for dim in dims %}
        <tr>
          <td>{{ loop.index }}</td>
          <td>{{ dim.name }}</td>
          <td>{{ dim.values|length }}</td>
        </tr>
      {% endfor %}
    </tbody>
  </table>
{% endblock %}

{% block scripts %}
<script>
  $.fn.editable.defaults.mode = 'inline';
  $(document).ready(function() {
      $('.x-editable-class').editable();
  });
</script>
{% endblock %}