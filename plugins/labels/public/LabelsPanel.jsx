import React from 'react';
import PropTypes from 'prop-types';
import L from 'leaflet';
import './LabelsPanel.scss';
import ErrorMessage from 'webodm/components/ErrorMessage';

export default class LabelsPanel extends React.Component {
  static defaultProps = {
  };
  static propTypes = {
    onClose: PropTypes.func.isRequired,
    tasks: PropTypes.object.isRequired,
    isShowed: PropTypes.bool.isRequired,
    map: PropTypes.object.isRequired
  }

  constructor(props){
    super(props);

    this.state = {
        error: "",
        permanentError: "",
        loading: true,
        task: props.tasks[0] || null,
        generateLoading: false,
        addingVerifiedLoading: false,
        previewLayer: null,
    };
  }

  componentDidUpdate(){
    if (this.props.isShowed && this.state.loading){
      const {id, project} = this.state.task;

      this.loadingReq = $.getJSON(`/api/projects/${project}/tasks/${id}/`)
          .done(res => {
              const { available_assets } = res;

              if (available_assets.indexOf("orthophoto.tif") === -1)
                this.setState({permanentError: "No Orthophoto is available. You need to have one to be able to label it."});
          })
          .fail(() => {
            this.setState({permanentError: `Cannot retrieve information for task ${id}. Are you are connected to the internet?`})
          })
          .always(() => {
            this.setState({loading: false});
            this.loadingReq = null;
          });
    }
  }

  componentWillUnmount(){
    if (this.loadingReq){
      this.loadingReq.abort();
      this.loadingReq = null;
    }
    if (this.generateReq){
      this.generateReq.abort();
      this.generateReq = null;
    }
  }

  waitForCompletion = (taskId, celery_task_id, cb) => {
    let errorCount = 0;

    const check = () => {
      $.ajax({
          type: 'GET',
          url: `/api/plugins/labels/task/${taskId}/labels/check/${celery_task_id}`
      }).done(result => {
          if (result.error || result.ready){
            cb(result);
          }else{
            // Retry
            setTimeout(() => check(), 2000);
          }
      }).fail(error => {
          console.warn(error);
          if (errorCount++ < 10) setTimeout(() => check(), 2000);
          else cb(JSON.stringify(error));
      });
    };

    check();
  }

  addVerified = () => {
    const { map } = this.props;
    const taskId = this.state.task.id;
    const url = `/api/plugins/labels/task/${taskId}/labels/verified`

    $.getJSON(url)
     .done((geojson) => {
      try{
        this.handleRemovePreview();
        
        if (geojson.features.length == 0) {
          throw 'Failed to find verified labels. Don\'t forget to verify them before loading them.'
        }

        this.setState({previewLayer: L.geoJSON(geojson, {
          onEachFeature: (feature, layer) => {
              layer.bindPopup(`<b>Name:</b> ${feature.properties.name}<BR><b>Attributes:</b> ${feature.properties.attributes}`);
          },
          style: feature => {
              return { color: "yellow" };
          }
        })});
        this.state.previewLayer.addTo(map);
        this.setState({['addingVerifiedLoading']: false});
      } catch(e) {
        this.setState({['addingVerifiedLoading']: false, 'error': e});
      }
     })
     .fail(error => this.setState({['addingVerifiedLoading']: false, 'error': error.responseJSON.error}));
  }

  handleRemovePreview = () => {
    const { map } = this.props;

    if (this.state.previewLayer){
      map.removeLayer(this.state.previewLayer);
      this.setState({previewLayer: null});
    }
  }

  generateLabelPath = () => {
    this.setState({['generateLoading']: true, error: ""});
    const taskId = this.state.task.id;

    this.generateReq = $.ajax({
        type: 'POST',
        url: `/api/plugins/labels/task/${taskId}/labels/generate`,
    }).done(result => {
        if (result.celery_task_id){
          this.waitForCompletion(taskId, result.celery_task_id, result => {
            if (result.error) {
              this.setState({['generateLoading']: false, error: result.error});
            } else {
              const url = `${window.location.protocol}//${window.location.hostname}:8080/LabelMeAnnotationTool/tool.html?folder=${result.folder}&image=${result.image}&actions=a&scribble=false&mode=i`;
              window.open(url,'_blank');
              this.setState({['generateLoading']: false});
            }
          });
        }else if (result.error){
            this.setState({['generateLoading']: false, error: result.error});
        }else{
            this.setState({['generateLoading']: false, error: "Invalid response: " + result});
        }
    }).fail(error => {
        this.setState({['generateLoading']: false, error: JSON.stringify(error)});
    });
  }

  render(){
    const { loading, task, error, permanentError, addingVerifiedLoading,
            generateLoading, previewLayer } = this.state;
    let content = "";
    if (loading) content = (<span><i className="fa fa-circle-o-notch fa-spin"></i> Loading...</span>);
    else if (permanentError) content = (<div className="alert alert-warning">{permanentError}</div>);
    else{
      content = (<div>
        <ErrorMessage bind={[this, "error"]} />
        <div className="row action-buttons">
          <div className="text-right">
            <button onClick={this.generateLabelPath}
                    disabled={generateLoading} type="button" className="btn btn-sm btn-primary btn-preview">
              {generateLoading ? <i className="fa fa-spin fa-circle-o-notch"/> : <i className="glyphicon glyphicon-pencil"/>} Start Labeling
            </button>
            <br/>
            <div className="col-sm-3">
              {previewLayer ? <a title="Delete Preview" href="javascript:void(0);" onClick={this.handleRemovePreview}>
                <i className="fa fa-trash"></i>
              </a> : ""}
            </div>
            <button onClick={this.addVerified}
                    disabled={addingVerifiedLoading} type="button" className="btn btn-sm btn-primary btn-preview">
              {addingVerifiedLoading ? <i className="fa fa-spin fa-circle-o-notch"/> : <i className="glyphicon glyphicon-cloud-download"/>} Load Verified Labels
            </button>
          </div>
        </div>
      </div>);
    }

    return (<div className="labels-panel">
      <span className="close-button" onClick={this.props.onClose}/>
      <div className="title">Labels</div>
      <hr/>
      {content}
    </div>);
  }
}