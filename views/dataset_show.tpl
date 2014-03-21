{% extends "base.tpl" %}
{% macro bold_if_ref(value) -%}
  {% if value.id %}
    <strong> {{ value.id }} </strong>
  {% else %}
    {{ value }}
  {% endif %}
{%- endmacro %}

{% block title %}Dataset{% endblock %}
{% block content %}
  <h1>Dataset</h1>
  {{ meta.id }}
  <h2>Properties</h2>
  
  <table class="table table-bordered table-striped">
    <thead>
      <tr>
          <th>Attribute</th>
          <th>Value</th>
      </tr>
    </thead>
    
    <tbody>
      {% for k, v in meta.properties %}
      <tr>
        <td>{{ bold_if_ref(k) }}</td>
        <td>{{ bold_if_ref(v) }}</td>
      </tr>
      {% endfor %}
    </tbody>
  </table>
  
  <h2>Dimensions</h2>
  <dl>
  {% for dim in meta.dims %}
    <dt>Dimension {{ loop.index }}</dt><dd>{{ dim.name }}</dd>
  {% endfor %}
  </dl>
  
{% endblock %}